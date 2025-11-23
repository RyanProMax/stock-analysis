from stockstats import StockDataFrame
import pandas as pd
from dataclasses import dataclass, field
from typing import List
import src.config as cfg


# 使用 @dataclass 装饰器自动生成构造函数等 boilerplate 代码
# 用于封装一次完整的分析结果
@dataclass
class AnalysisReport:
    symbol: str  # 股票代码
    price: float  # 分析时的最新价格
    score: int  # 基于多因子策略计算出的综合得分
    advice: str  # 根据得分生成的最终投资建议 (如：买入、卖出、观望)
    bullish_signals: List[str] = field(
        default_factory=list
    )  # 看涨信号描述列表，默认为空列表
    bearish_signals: List[str] = field(
        default_factory=list
    )  # 看跌信号描述列表，默认为空列表


class StockAnalyzer:
    def __init__(self, df: pd.DataFrame, symbol: str):
        self.raw_df = df
        self.symbol = symbol
        # 将原始 DataFrame 转换为 StockDataFrame 对象
        self.stock = StockDataFrame.retype(df.copy())

    def analyze(self) -> AnalysisReport:
        """
        执行多因子综合分析，并返回一个 AnalysisReport 对象
        """

        # 最新的收盘价
        close = self.stock["close"].iloc[-1].item()

        # 获取最新的 MACD (平滑异同移动平均线) 指标
        macd = self.stock["macd"].iloc[-1].item()  # MACD 线的值
        macdh = self.stock["macdh"].iloc[-1].item()  # MACD 柱状图的值 (DIFF - DEA)

        # 获取最新的 RSI (相对强弱指数)，这里使用 stockstats 默认的14日周期
        rsi = self.stock["rsi_14"].iloc[-1].item()

        # 获取最新的 KDJ (随机指标)
        k = self.stock["kdjk"].iloc[-1].item()  # K 值
        d = self.stock["kdjd"].iloc[-1].item()  # D 值
        j = self.stock["kdjj"].iloc[-1].item()  # J 值

        # 获取最新的布林带 (Bollinger Bands) 指标
        boll_lb = self.stock["boll_lb"].iloc[-1].item()  # 布林带下轨 (Lower Band)
        boll_ub = self.stock["boll_ub"].iloc[-1].item()  # 布林带上轨 (Upper Band)

        # --- 逻辑打分 ---
        score = 0  # 初始化总分
        bull_signals = []  # 初始化看涨信号列表
        bear_signals = []  # 初始化看跌信号列表

        # 策略 A: MACD 趋势判断
        # 如果 MACD 值大于 0 (在零轴上方) 并且 MACD 柱也大于 0 (红柱)，认为是明确的多头趋势
        if macd > 0 and macdh > 0:
            score += 25  # 增加分数
            bull_signals.append(f"MACD 处于多头区域且红柱持续 (MACD={macd:.2f})")
        # 如果 MACD 值小于 0 (在零轴下方)，认为是空头趋势
        elif macd < 0:
            score -= 15  # 减少分数
            bear_signals.append(f"MACD 处于零轴下方空头趋势 (MACD={macd:.2f})")

        # 策略 B: RSI 情绪判断
        # 如果 RSI 小于配置文件中定义的超卖阈值 (如 30)
        if rsi < cfg.RSI_OVERSOLD:
            score += 30  # 大幅加分，认为市场超卖，可能即将反弹
            bull_signals.append(f"RSI 进入超卖区 ({rsi:.2f})，市场极度恐慌，反弹概率大")
        # 如果 RSI 大于配置文件中定义的超买阈值 (如 70)
        elif rsi > cfg.RSI_OVERBOUGHT:
            score -= 20  # 大幅减分，认为市场超买，回调风险高
            bear_signals.append(f"RSI 进入超买区 ({rsi:.2f})，谨防高位回调")

        # 策略 C: KDJ 短线买卖信号
        # 如果 J 值小于配置文件中定义的超卖阈值 (如 0 或 10)
        if j < cfg.KDJ_J_OVERSOLD:
            score += 20  # 加分，认为股票短线超跌，可能出现买入机会
            bull_signals.append(f"KDJ J值({j:.2f}) 进入超卖区，短线超跌")
        # 如果 J 值大于配置文件中定义的超买阈值 (如 90 或 100)
        elif j > cfg.KDJ_J_OVERBOUGHT:
            score -= 15  # 减分，认为股票短线过热，可能出现卖出机会
            bear_signals.append(f"KDJ J值({j:.2f}) 进入超买区，短线过热")

        # 策略 D: 布林带位置 (用于判断极端行情，寻找抄底或逃顶机会)
        # 如果收盘价跌破布林带下轨，是经典的抄底信号之一
        if close < boll_lb:
            score += 25  # 大幅加分，认为价格偏离过大，有向中轨回归的强烈需求
            bull_signals.append("股价跌破布林下轨，是潜在的买入机会")
        # 如果收盘价突破布林带上轨，是潜在的顶部信号
        elif close > boll_ub:
            score -= 10  # 减分，认为价格可能面临回调压力
            bear_signals.append("股价突破布林上轨，注意回落风险")

        # --- 3. 根据总分生成综合投资建议 ---
        if score >= 60:
            advice = "🚀 强烈买入 (Strong Buy)"
        elif score >= 20:
            advice = "📈 谨慎看多 (Buy/Hold)"
        elif score > -20:
            advice = "👀 观望 (Neutral)"
        else:
            advice = "📉 建议卖出/规避 (Sell)"

        return AnalysisReport(
            symbol=self.symbol,
            price=close,
            score=score,
            advice=advice,
            bullish_signals=bull_signals,
            bearish_signals=bear_signals,
        )
