from stockstats import StockDataFrame
import pandas as pd
from dataclasses import dataclass, field
from typing import List
import src.config as cfg


@dataclass
class AnalysisReport:
    symbol: str
    price: float  # 确保这里是 float 类型
    score: int
    advice: str
    bullish_signals: List[str] = field(default_factory=list)
    bearish_signals: List[str] = field(default_factory=list)


class StockAnalyzer:
    def __init__(self, df: pd.DataFrame, symbol: str):
        self.raw_df = df
        self.symbol = symbol
        # 初始化 StockDataFrame (Stockstats 的核心)
        self.stock = StockDataFrame.retype(df.copy())

    def analyze(self) -> AnalysisReport:
        """
        执行多因子综合分析
        """
        # --- 1. 获取最新指标 ---
        # 🟢 修正点：全部加上 .item() 来强制提取 Python float 标量值

        close = self.stock["close"].iloc[-1].item()

        # MACD
        macd = self.stock["macd"].iloc[-1].item()
        macdh = self.stock["macdh"].iloc[-1].item()

        # RSI
        rsi = self.stock["rsi_14"].iloc[-1].item()

        # KDJ
        k = self.stock["kdjk"].iloc[-1].item()
        d = self.stock["kdjd"].iloc[-1].item()
        j = self.stock["kdjj"].iloc[-1].item()

        # Bollinger Bands
        boll_lb = self.stock["boll_lb"].iloc[-1].item()
        boll_ub = self.stock["boll_ub"].iloc[-1].item()

        # --- 2. 逻辑打分引擎 ---
        score = 0
        bull_signals = []
        bear_signals = []

        # 策略 A: MACD 趋势判断 (现在 macd/macdh 已经是 float，比较正常)
        if macd > 0 and macdh > 0:
            score += 25
            bull_signals.append(f"MACD 处于多头区域且红柱持续 (MACD={macd:.2f})")
        elif macd < 0:
            score -= 15
            bear_signals.append(f"MACD 处于零轴下方空头趋势 (MACD={macd:.2f})")

        # 策略 B: RSI 情绪判断
        if rsi < cfg.RSI_OVERSOLD:
            score += 30
            bull_signals.append(f"RSI 进入超卖区 ({rsi:.2f})，市场极度恐慌，反弹概率大")
        elif rsi > cfg.RSI_OVERBOUGHT:
            score -= 20
            bear_signals.append(f"RSI 进入超买区 ({rsi:.2f})，谨防高位回调")

        # 策略 C: KDJ 短线买卖
        if j < cfg.KDJ_J_OVERSOLD:
            score += 20
            bull_signals.append(f"KDJ J值({j:.2f}) 底背离，短线超跌")
        elif j > cfg.KDJ_J_OVERBOUGHT:
            score -= 15
            bear_signals.append(f"KDJ J值({j:.2f}) 钝化，短线过热")

        # 策略 D: 布林带位置 (抄底/逃顶)
        if close < boll_lb:
            score += 25
            bull_signals.append("股价跌破布林下轨，概率回归中轨")
        elif close > boll_ub:
            score -= 10
            bear_signals.append("股价突破布林上轨，注意回落风险")

        # --- 3. 生成综合建议 ---
        if score >= 60:
            advice = "🚀 强烈买入 (Strong Buy)"
        elif score >= 20:
            advice = "📈 谨慎看多 (Buy/Hold)"
        elif score > -20:
            advice = "👀 观望 (Neutral)"
        else:
            advice = "📉 建议卖出/规避 (Sell)"

        # 这里的 price=close 现在是 float，匹配 AnalysisReport 要求
        return AnalysisReport(
            symbol=self.symbol,
            price=close,
            score=score,
            advice=advice,
            bullish_signals=bull_signals,
            bearish_signals=bear_signals,
        )
