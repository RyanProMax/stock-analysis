from stockstats import StockDataFrame
import pandas as pd

from .model import cfg, AnalysisReport
from .report import print_report


class StockAnalyzer:
    INDICATORS_TO_CALCULATE = [
        "macd",
        "macdh",
        "macds",
        "rsi_14",
        "kdjk",
        "kdjd",
        "kdjj",
        "boll",
        "boll_ub",
        "boll_lb",
        "close_5_sma",
        "close_10_sma",
        "close_20_sma",
        "close_60_sma",
        "vr",
        "wr_14",
        "atr",
        "volume",
    ]

    def __init__(self, df: pd.DataFrame, symbol: str, stock_name: str):
        self.raw_df = df
        self.symbol = symbol
        self.stock_name = stock_name
        self.stock = StockDataFrame.retype(df.copy())

        for indicator in self.INDICATORS_TO_CALCULATE:
            self.stock.get(indicator)

    # 贪恐指数计算
    def _calculate_fear_greed(self, row, close) -> tuple[float, str]:
        """
        计算个股情绪指数 (0-100)
        逻辑：RSI(40%) + Bollinger%B(40%) + WR(20%)
        """
        # 1. RSI (0-100)
        rsi = row.get("rsi_14", 50)

        # 2. 布林带位置 %B (归一化到 0-100)
        lb = row.get("boll_lb", close * 0.9)
        ub = row.get("boll_ub", close * 1.1)
        if ub != lb:
            pct_b = (close - lb) / (ub - lb) * 100
        else:
            pct_b = 50
        pct_b = max(0, min(100, pct_b))  # 截断极端值

        # 3. 威廉指标 WR (-100 到 0) -> 映射为 (0 到 100)
        wr = row.get("wr_14", -50)
        wr_score = wr + 100

        # 合成指数
        fg_index = (rsi * 0.4) + (pct_b * 0.4) + (wr_score * 0.2)

        # 生成标签
        if fg_index <= 20:
            label = "🥶 极度恐慌"
        elif fg_index <= 40:
            label = "😨 恐慌"
        elif fg_index <= 60:
            label = "😐 中性"
        elif fg_index <= 80:
            label = "🤤 贪婪"
        else:
            label = "🔥 极度贪婪"

        return fg_index, label

    def analyze(self) -> AnalysisReport | None:
        last_row = self.stock.iloc[-1]
        prev_row = self.stock.iloc[-2] if len(self.stock) > 1 else last_row

        close = float(last_row.get("close", 0.0))
        if close == 0.0:
            return None

        # --- 提取原有指标 ---
        macd_h = last_row.get("macdh", 0.0)
        rsi = last_row.get("rsi_14", 50.0)
        wr = last_row.get("wr_14", -50.0)
        ma5 = last_row.get("close_5_sma", 0)
        ma20 = last_row.get("close_20_sma", 0)
        ma60 = last_row.get("close_60_sma", 0)
        atr = last_row.get("atr", 0)
        boll_lb = last_row.get("boll_lb", 0)
        boll_ub = last_row.get("boll_ub", 0)

        fg_index, fg_label = self._calculate_fear_greed(last_row, close)

        # 初始基础分
        score = 50
        bull_signals = []
        bear_signals = []

        # 1. 趋势判定 (权重最高: 40分)
        # 逻辑：不做逆势单，均线多头排列才给高分
        trend_status = "震荡/不明确"
        if close > ma20 and ma20 > ma60:
            score += 20
            trend_status = "📈 多头趋势 (中期看涨)"
            bull_signals.append("价格站上 MA20/MA60，趋势向好")
        elif close < ma20 and ma20 < ma60:
            score -= 20
            trend_status = "📉 空头趋势 (中期看跌)"
            bear_signals.append("价格跌破 MA20/MA60，趋势走坏")

        if close > ma5:
            score += 5
        else:
            score -= 5

        # 2. 动能与超买超卖 (权重: 30分)
        # MACD
        if macd_h > 0:
            score += 5
            if macd_h > prev_row.get("macdh", 0):
                bull_signals.append("MACD 动能增强")
        else:
            score -= 5

        # RSI (结合趋势过滤)
        if rsi < cfg.RSI_OVERSOLD:
            # 在多头趋势中，超卖是黄金坑；在空头趋势中，超卖可能还要跌
            if close > ma60:
                score += 20
                bull_signals.append(f"RSI超卖 ({rsi:.1f}) + 趋势向上 = 黄金买点")
            else:
                score += 10
                bull_signals.append(f"RSI超卖 ({rsi:.1f})，存在反弹需求")
        elif rsi > cfg.RSI_OVERBOUGHT:
            score -= 15
            bear_signals.append(f"RSI超买 ({rsi:.1f})，注意回调")

        # 威廉指标 W&R (灵敏度高)
        if wr < -80:  # 超卖
            score += 5
            bull_signals.append(f"WR进入底部区域 ({wr:.1f})")
        elif wr > -20:  # 超买
            score -= 5

        # 3. 价格形态与量能 (权重: 20分)
        # 布林带
        if close <= boll_lb * 1.01:
            score += 10
            bull_signals.append("股价触及布林下轨，支撑较强")
        elif close >= boll_ub * 0.99:
            score -= 10
            bear_signals.append("股价触及布林上轨，压力较大")

        # 贪恐指数逆向策略
        if fg_index < 20:
            score += 15
            bull_signals.append(f"情绪极度恐慌 ({fg_index:.0f})，往往是阶段性底部")
        elif fg_index > 80:
            score -= 15
            bear_signals.append(f"情绪极度贪婪 ({fg_index:.0f})，警惕高位获利回吐")

        # 4. 风险风控计算 (ATR)
        # 建议止损价 = 当前价 - 2倍ATR (常规波动范围之外)
        stop_loss = close - (2 * atr) if atr > 0 else close * 0.95
        score = max(0, min(100, score))

        # --- 生成建议 ---
        if score >= cfg.STRONG_BUY_SCORE:
            advice = "🚀 强烈买入 (Strong Buy)"
        elif score >= cfg.BUY_SCORE:
            advice = "📈 建议买入 (Buy)"
        elif score >= cfg.NEUTRAL_SCORE:
            advice = "👀 观望/持有 (Hold)"
        elif score >= cfg.STRONG_SELL_SCORE:
            advice = "📉 建议减仓 (Sell)"
        else:
            advice = "🏃‍♂️ 坚决清仓 (Strong Sell)"

        final_cols = [
            c
            for c in ["open", "close", "high", "low", "volume"]
            + self.INDICATORS_TO_CALCULATE
            if c in self.stock.columns
        ]

        report = AnalysisReport(
            symbol=self.symbol,
            stock_name=self.stock_name,
            price=close,
            score=score,
            advice=advice,
            trend_status=trend_status,
            stop_loss_price=stop_loss,
            data_and_indicators=self.stock[final_cols],
            bullish_signals=bull_signals,
            bearish_signals=bear_signals,
            fear_greed_index=fg_index,
            fear_greed_label=fg_label,
        )

        print_report(report)
        return report
