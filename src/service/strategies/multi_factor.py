from stockstats import StockDataFrame
import pandas as pd

from ..model import cfg, AnalysisReport
from ..report import print_report
from .base import BaseStockAnalyzer


class MultiFactorAnalyzer(BaseStockAnalyzer):
    """
    多因子技术分析策略（继承自 BaseStockAnalyzer）

    核心设计理念：
    1. 多因子分类：将技术指标分为趋势、波动率、动量、量能四大类
    2. 去相关性处理：同类指标先标准化评分后取平均，避免重复计算
    3. 等权合成：四大因子组等权重汇总为最终 0-100 综合得分
    4. 信号输出：每个因子组独立输出多/空信号，便于理解评分来源

    这是默认的策略实现，后续可以扩展其他策略类（如机器学习策略、量化策略等）
    """

    # 需要计算的技术指标列表（按因子分类）
    INDICATORS_TO_CALCULATE = [
        # 趋势指标
        "macd",  # MACD 主线
        "macdh",  # MACD 柱线（用于趋势判断）
        "macds",  # MACD 信号线
        "close_12_ema",  # 12日指数均线
        "close_26_ema",  # 26日指数均线
        "close_5_sma",  # 5日简单均线
        "close_10_sma",  # 10日简单均线
        "close_20_sma",  # 20日简单均线
        "close_60_sma",  # 60日简单均线
        # 动量指标
        "rsi_14",  # 14日 RSI 相对强弱指标
        "kdjk",  # KDJ 指标 K 值
        "kdjd",  # KDJ 指标 D 值
        "kdjj",  # KDJ 指标 J 值
        "wr_14",  # 14日威廉指标
        # 波动率指标
        "boll",  # 布林带中轨
        "boll_ub",  # 布林带上轨
        "boll_lb",  # 布林带下轨
        "atr",  # 真实波动幅度（用于止损计算）
        # 量能指标
        "vr",  # 成交量比率
        "volume",  # 成交量
    ]

    def __init__(self, df: pd.DataFrame, symbol: str, stock_name: str):
        """
        初始化多因子分析器

        Args:
            df: 股票行情数据 DataFrame
            symbol: 股票代码
            stock_name: 股票名称
        """
        # 调用父类初始化，进行输入验证
        super().__init__(df, symbol, stock_name)

        # 初始化技术指标计算引擎
        self.stock = StockDataFrame.retype(self.raw_df.copy())

        # 计算所需的技术指标
        for indicator in self.INDICATORS_TO_CALCULATE:
            self.stock.get(indicator)

    def _score_trend(
        self, last_row, prev_row, close: float
    ) -> tuple[int, str, list[str], list[str]]:
        """
        趋势因子评分（权重：25%）

        评估指标：
        - MA 均线系统：MA5/MA20/MA60 多头/空头排列
        - EMA 指数均线：12日/26日 EMA 交叉信号
        - MACD 动能：柱线（MACDH）方向与强度

        去相关性：三个子指标标准化后取平均，避免均线类指标重复计算
        """
        bull, bear = [], []
        ma5 = last_row.get("close_5_sma", close)
        ma20 = last_row.get("close_20_sma", close)
        ma60 = last_row.get("close_60_sma", close)

        components = []
        trend_status = "震荡/不明确"

        if close > ma20 and ma20 > ma60:
            components.append(1.0)
            trend_status = "📈 多头趋势 (中期看涨)"
            bull.append("价格站上 MA20/MA60，趋势排列良好")
        elif close < ma20 and ma20 < ma60:
            components.append(0.0)
            trend_status = "📉 空头趋势 (中期看跌)"
            bear.append("价格跌破 MA20/MA60，趋势走弱")
        else:
            components.append(0.5)

        components.append(1.0 if close > ma5 else 0.0)

        ema12 = last_row.get("close_12_ema", close)
        ema26 = last_row.get("close_26_ema", close)
        if ema12 > ema26 * 1.01:
            components.append(1.0)
            bull.append("12 日 EMA 上穿 26 日 EMA")
        elif ema12 < ema26 * 0.99:
            components.append(0.0)
            bear.append("12 日 EMA 跌破 26 日 EMA")
        else:
            components.append(0.5)

        macd_h = last_row.get("macdh", 0.0)
        prev_macd_h = prev_row.get("macdh", macd_h)
        if macd_h > 0 and macd_h >= prev_macd_h:
            components.append(1.0)
            bull.append("MACD 柱线抬升，动能增强")
        elif macd_h < 0 and macd_h <= prev_macd_h:
            components.append(0.0)
            bear.append("MACD 柱线走弱，动能衰减")
        else:
            components.append(0.5)

        return self._average_score(components), trend_status, bull, bear

    def _score_volatility(
        self, last_row, close: float, fg_index: float
    ) -> tuple[int, list[str], list[str]]:
        """
        波动率因子评分（权重：25%）

        评估指标：
        - 布林带宽度：衡量波动率健康度（5%-18% 为理想区间）
        - 布林带位置（%B）：价格在通道内的相对位置（下轨支撑/上轨压力）
        - ATR 真实波动幅度：评估波动剧烈程度，用于风险控制
        - 贪恐指数：逆向情绪指标（恐慌买入/贪婪卖出）

        去相关性：四个子指标标准化后取平均
        """
        bull, bear = [], []
        lb = last_row.get("boll_lb", close * 0.9)
        ub = last_row.get("boll_ub", close * 1.1)

        band_width = (ub - lb) / close if close > 0 and ub > lb else 0.0
        if 0.05 <= band_width <= 0.18:
            width_score = 0.8
            bull.append("布林带宽度处于健康波动区间")
        elif band_width < 0.05:
            width_score = 0.5
            bear.append("波动率偏低，方向感不足")
        else:
            width_score = 0.3
            bear.append("波动率过高，短期风险放大")

        if ub > lb:
            pct_b = self._clamp_ratio((close - lb) / (ub - lb))
        else:
            pct_b = 0.5
        if pct_b <= 0.2:
            pos_score = 0.9
            bull.append("价格贴近布林下轨，存在支撑")
        elif pct_b >= 0.8:
            pos_score = 0.1
            bear.append("价格逼近布林上轨，压力较大")
        else:
            pos_score = 0.6

        atr = last_row.get("atr", 0.0)
        atr_ratio = atr / close if close > 0 else 0.0
        if 0.015 <= atr_ratio <= 0.05:
            atr_score = 0.8
        elif atr_ratio > 0.08:
            atr_score = 0.3
            bear.append("ATR 显示波动剧烈，注意止损")
        else:
            atr_score = 0.6

        if fg_index <= 20:
            fg_score = 0.85
            bull.append(f"情绪极度恐慌 ({fg_index:.0f})，具备逆向价值")
        elif fg_index >= 80:
            fg_score = 0.2
            bear.append(f"情绪极度贪婪 ({fg_index:.0f})，警惕回调")
        else:
            fg_score = 0.6

        score = self._average_score([width_score, pos_score, atr_score, fg_score])
        return score, bull, bear

    def _score_momentum(self, last_row) -> tuple[int, list[str], list[str]]:
        """
        动量因子评分（权重：25%）

        评估指标：
        - RSI 相对强弱指标：超买超卖判断（45-60 为最佳区间）
        - KDJ 随机指标：J 线形态与 K/D 交叉信号
        - WR 威廉指标：短期超买超卖灵敏度高
        - MACD 主线：趋势动能方向（正值看多/负值看空）

        去相关性：四个动量指标标准化后取平均，避免重复计算超买超卖信号
        """
        bull, bear = [], []
        components = []

        rsi = last_row.get("rsi_14", 50.0)
        if 45 <= rsi <= 60:
            components.append(0.9)
        elif rsi < cfg.RSI_OVERSOLD:
            components.append(0.75)
            bull.append(f"RSI 超卖 ({rsi:.1f})，反弹概率高")
        elif rsi > cfg.RSI_OVERBOUGHT:
            components.append(0.2)
            bear.append(f"RSI 超买 ({rsi:.1f})，易回调")
        else:
            components.append(0.5)

        kdjk = last_row.get("kdjk", 50.0)
        kdjd = last_row.get("kdjd", 50.0)
        kdjj = last_row.get("kdjj", 50.0)
        if kdjk > kdjd and kdjj > kdjk:
            components.append(0.8)
            bull.append("KDJ 多头形态，J 线上穿")
        elif kdjk < kdjd and kdjj < kdjd:
            components.append(0.2)
            bear.append("KDJ 空头形态，J 下穿")
        else:
            components.append(0.5)

        wr = last_row.get("wr_14", -50.0)
        if wr <= -80:
            components.append(0.85)
            bull.append(f"WR 进入底部区域 ({wr:.1f})")
        elif wr >= -20:
            components.append(0.2)
            bear.append(f"WR 逼近顶部区域 ({wr:.1f})")
        else:
            components.append(0.5)

        macd = last_row.get("macd", 0.0)
        if macd > 0:
            components.append(0.7)
        elif macd < 0:
            components.append(0.3)
        else:
            components.append(0.5)

        score = self._average_score(components)
        return score, bull, bear

    def _score_volume(
        self, last_row, volume_ma5: float, volume_ma20: float
    ) -> tuple[int, list[str], list[str]]:
        """
        量能因子评分（权重：25%）

        评估指标：
        - 短期量能比：当前成交量 vs 5日均量（1.5倍以上为放量）
        - 中期量能比：5日均量 vs 20日均量（判断资金流入趋势）
        - VR 成交量比率：买盘/卖盘力量对比（>160 买盘占优，<70 卖压大）

        去相关性：三个量能指标标准化后取平均
        """
        bull, bear = [], []
        components = []

        current_volume = float(last_row.get("volume", volume_ma5))
        if volume_ma5 > 0:
            short_ratio = current_volume / volume_ma5
        else:
            short_ratio = 1.0

        if short_ratio >= 1.5:
            components.append(0.85)
            bull.append("量能放大到 5 日均量 1.5 倍以上")
        elif short_ratio <= 0.6:
            components.append(0.3)
            bear.append("量能萎缩到 5 日均量 0.6 倍以下")
        else:
            components.append(0.55)

        if volume_ma20 > 0:
            mid_ratio = volume_ma5 / volume_ma20
        else:
            mid_ratio = 1.0

        if mid_ratio >= 1.2:
            components.append(0.75)
            bull.append("短期均量高于中期均量，资金净流入")
        elif mid_ratio <= 0.8:
            components.append(0.3)
            bear.append("短期均量低于中期均量，资金趋冷")
        else:
            components.append(0.5)

        vr = last_row.get("vr", 100.0)
        if vr >= 160:
            components.append(0.8)
            bull.append(f"VR={vr:.0f}，买盘明显占优")
        elif vr <= 70:
            components.append(0.25)
            bear.append(f"VR={vr:.0f}，抛压大于买盘")
        else:
            components.append(0.55)

        score = self._average_score(components)
        return score, bull, bear

    def _calculate_fear_greed(self, row, close) -> tuple[float, str]:
        """
        计算个股贪恐指数（Fear & Greed Index）

        用途：衡量市场情绪，用于逆向策略（恐慌买入/贪婪卖出）
        范围：0-100（0=极度恐慌，100=极度贪婪）

        合成逻辑：
        - RSI 相对强弱指标（40%）：反映超买超卖状态
        - 布林带位置 %B（40%）：价格在通道内的相对位置
        - WR 威廉指标（20%）：短期超买超卖灵敏度

        注意：该指数用于波动率因子评分，而非独立因子
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
        """
        执行完整的股票技术分析流程

        核心流程：
        1. 提取最新行情数据和技术指标
        2. 计算贪恐指数（用于波动率因子）
        3. 分别计算四大因子得分（趋势/波动率/动量/量能）
        4. 等权合成最终综合得分（0-100）
        5. 汇总多/空信号并生成交易建议

        等权合成逻辑：
        - 每个因子组权重 25%（1/4）
        - 最终得分 = (趋势分 + 波动率分 + 动量分 + 量能分) / 4
        - 避免单一因子过度影响，保持策略平衡性
        """
        last_row = self.stock.iloc[-1]
        prev_row = self.stock.iloc[-2] if len(self.stock) > 1 else last_row

        close = float(last_row.get("close", 0.0))
        if close == 0.0:
            return None

        # --- 提取基础指标数据 ---
        macd_h = last_row.get("macdh", 0.0)
        rsi = last_row.get("rsi_14", 50.0)
        wr = last_row.get("wr_14", -50.0)
        ma5 = last_row.get("close_5_sma", 0)
        ma20 = last_row.get("close_20_sma", 0)
        ma60 = last_row.get("close_60_sma", 0)
        atr = last_row.get("atr", 0)
        boll_lb = last_row.get("boll_lb", 0)
        boll_ub = last_row.get("boll_ub", 0)

        # 计算贪恐指数（用于波动率因子评分）
        fg_index, fg_label = self._calculate_fear_greed(last_row, close)

        # 计算成交量均线（用于量能因子评分）
        volume_series = (
            self.raw_df["volume"]
            if "volume" in self.raw_df.columns
            else pd.Series([last_row.get("volume", 0)])
        )
        volume_series = volume_series.fillna(method="ffill").fillna(0)
        volume_ma5 = float(volume_series.tail(5).mean())
        volume_ma20 = (
            float(volume_series.tail(20).mean())
            if len(volume_series) >= 20
            else volume_ma5
        )

        # --- 四大因子评分（每个因子组内部已做去相关性处理）---
        trend_score, trend_status, trend_bull, trend_bear = self._score_trend(
            last_row, prev_row, close
        )
        vol_score, vol_bull, vol_bear = self._score_volatility(
            last_row, close, fg_index
        )
        momentum_score, momentum_bull, momentum_bear = self._score_momentum(last_row)
        volume_score, volume_bull, volume_bear = self._score_volume(
            last_row, volume_ma5, volume_ma20
        )

        # --- 等权合成最终得分（四大因子各占 25% 权重）---
        group_scores = {
            "trend": trend_score,
            "volatility": vol_score,
            "momentum": momentum_score,
            "volume": volume_score,
        }
        score = int(round(sum(group_scores.values()) / len(group_scores)))

        # --- 汇总多/空信号（便于理解评分来源）---
        bull_signals = trend_bull + vol_bull + momentum_bull + volume_bull
        bear_signals = trend_bear + vol_bear + momentum_bear + volume_bear

        # --- 计算动态止损价（基于 ATR 风险控制）---
        atr = last_row.get("atr", 0)
        stop_loss = close - (2 * atr) if atr > 0 else close * 0.95

        # --- 根据综合得分生成交易建议 ---
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
