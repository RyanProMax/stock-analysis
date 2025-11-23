from stockstats import StockDataFrame
import pandas as pd
from dataclasses import dataclass, field

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from typing import List, Optional
import src.config as cfg


@dataclass
class AnalysisReport:
    """封装单次完整的股票分析结果，包括原始数据、指标和建议。"""

    symbol: str  # 股票代码
    price: float  # 分析时的最新价格
    score: int  # 基于多因子策略计算出的综合得分
    advice: str  # 根据得分生成的最终投资建议 (如：买入、卖出、观望)
    # 存储包含日期、开盘、收盘、最高、最低以及所有计算因子指标的 DataFrame
    data_and_indicators: Optional[pd.DataFrame] = None
    bullish_signals: List[str] = field(default_factory=list)  # 看涨信号描述列表
    bearish_signals: List[str] = field(default_factory=list)  # 看跌信号描述列表


class StockAnalyzer:
    # 预定义需要计算的所有指标名称
    # stockstats 在计算这些指标时，会自动依赖于'open', 'close', 'high', 'low', 'volume'
    INDICATORS_TO_CALCULATE = [
        "macd",
        "macdh",
        "macds",  # MACD
        "rsi_14",  # RSI (默认14日)
        "kdjk",
        "kdjd",
        "kdjj",  # KDJ (默认9日)
        "boll",
        "boll_ub",
        "boll_lb",  # Bollinger Bands (默认20日)
        # "dma",
        # "pdi",
        # "mdi",
        # "dx",  # 其他常用指标 (DMA, DMI等)
        # "tr",
        # "atr",  # ATR
    ]

    def __init__(self, df: pd.DataFrame, symbol: str, stock_name: str):
        self.raw_df = df
        self.symbol = symbol
        self.stock_name = stock_name
        # 将原始 DataFrame 转换为 StockDataFrame 对象
        self.stock = StockDataFrame.retype(df.copy())

        # 提前计算所有所需的指标
        for indicator in self.INDICATORS_TO_CALCULATE:
            self.stock.get(indicator)

    def analyze(self) -> AnalysisReport:
        """
        执行多因子综合分析，并返回一个 AnalysisReport 对象
        """
        # 提取最后一行数据（包含元数据和所有计算的因子指标）
        last_row = self.stock.iloc[-1]

        # 提取关键指标值
        close = float(last_row.get("close", 0.0))
        if close == 0.0:
            print(f"Warning: Close price is 0 or missing for {self.symbol}")

        macd = last_row.get("macd", 0.0)
        macdh = last_row.get("macdh", 0.0)
        rsi = last_row.get("rsi_14", 50.0)
        k = last_row.get("kdjk", 50.0)
        d = last_row.get("kdjd", 50.0)
        j = last_row.get("kdjj", 50.0)
        boll_lb = last_row.get("boll_lb", close * 0.9)  # 默认值应谨慎设置
        boll_ub = last_row.get("boll_ub", close * 1.1)

        # --- 逻辑打分 ---
        score = 0  # 初始化总分
        bull_signals = []  # 初始化看涨信号列表
        bear_signals = []  # 初始化看跌信号列表

        # 策略 A: MACD 趋势判断
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

        # 策略 C: KDJ 短线买卖信号
        if j < cfg.KDJ_J_OVERSOLD:
            score += 20
            bull_signals.append(f"KDJ J值({j:.2f}) 进入超卖区，短线超跌")
        elif j > cfg.KDJ_J_OVERBOUGHT:
            score -= 15
            bear_signals.append(f"KDJ J值({j:.2f}) 进入超买区，短线过热")

        # 策略 D: 布林带位置
        if close < boll_lb:
            score += 25
            bull_signals.append("股价跌破布林下轨，是潜在的买入机会")
        elif close > boll_ub:
            score -= 10
            bear_signals.append("股价突破布林上轨，注意回落风险")

        # --- 根据总分生成综合投资建议 ---
        if score >= cfg.STRONG_BUY_SCORE:
            advice = "🚀 强烈买入 (Strong Buy)"
        elif score >= cfg.HOLD_SCORE:
            advice = "📈 谨慎看多 (Buy/Hold)"
        elif score > cfg.NEUTRAL_SCORE:
            advice = "👀 观望 (Neutral)"
        else:
            advice = "📉 建议卖出/规避 (Sell)"

        # 确保 data_and_indicators 仅包含元数据和计算后的指标
        columns_to_keep = [
            "open",
            "close",
            "high",
            "low",
            "volume",
        ] + self.INDICATORS_TO_CALCULATE
        # 筛选出DataFrame中实际存在的列
        final_df = self.stock[
            [col for col in columns_to_keep if col in self.stock.columns]
        ]

        report = AnalysisReport(
            symbol=self.symbol,
            price=close,
            score=score,
            advice=advice,
            data_and_indicators=final_df,  # 返回包含所有数据的完整 DataFrame
            bullish_signals=bull_signals,
            bearish_signals=bear_signals,
        )
        self.print_report(report)

        return report

    def print_report(self, report: AnalysisReport):
        # --- 指标表格 ---
        if report.data_and_indicators is not None:
            table = Table(
                box=box.SIMPLE_HEAVY,
                show_header=True,
                header_style="bold cyan",
            )
            table.add_column("指标名称")
            table.add_column("数值", justify="left", style="bold")
            table.add_column("状态/参考", justify="left")
            last = report.data_and_indicators.iloc[-1]
            rsi = last.get("rsi_14", 50)
            k, d, j = last.get("kdjk", 0), last.get("kdjd", 0), last.get("kdjj", 0)

            # 添加行数据
            table.add_row("最新价格", f"¥ {report.price:.2f}", "")
            table.add_row("成交量", f"{int(last['volume'])/10000:.2f} 万", "")
            # 分隔线
            table.add_section()

            table.add_row(
                "MACD 趋势",
                f"{last.get('macd',0):.2f}",
                "",
            )
            table.add_row("MACD 动能", f"{last.get('macdh',0):.2f}", "")
            table.add_row(
                "RSI (14)",
                f"{rsi:.2f}",
                f"{'[red]🔴 超买[/]' if rsi > 70 else ('[green]🟢 超卖[/]' if rsi < 30 else '[yellow]🟡 中性[/]')}",
            )
            table.add_row(
                "KDJ (J)",
                f"{last.get('kdjj',0):.2f}",
                f"{'[red]🔴 超买[/]' if j > 100 else ('[green]🟢 超卖(机会)[/]' if j < 0 else '[yellow]🟡 中性[/]')}",
            )
            table.add_row("KDJ (K/D)", f"{k:.1f} / {d:.1f}" "")
            table.add_row(
                "布林上轨", f"{last.get('boll_ub',0):.2f}", "[magenta]压力位[/]"
            )
            table.add_row(
                "布林下轨", f"{last.get('boll_lb',0):.2f}", "[magenta]支撑位[/]"
            )

            # --- 组装信号文本 ---
            bull_text = (
                "\n".join([f"✅ {s}" for s in report.bullish_signals])
                if report.bullish_signals
                else "[dim]无明显看涨信号[/]"
            )
            bear_text = (
                "\n".join([f"❌ {s}" for s in report.bearish_signals])
                if report.bearish_signals
                else "[dim]无明显看跌信号[/]"
            )

            # --- 打印组合面板 ---
            # 顶部摘要
            score_color = (
                "red"
                if report.score < cfg.STRONG_SELL_SCORE
                else ("green" if report.score >= cfg.STRONG_BUY_SCORE else "yellow")
            )

            summary_panel = Panel(
                f"📅 数据日期: [bold]{report.data_and_indicators.index[-1].strftime('%Y-%m-%d')}[/]\n"
                f"💰 股票代码: [bold]{report.symbol}[/]\n"
                f"💸 股票名称: [bold]{self.stock_name}[/]\n"
                f"🏆 综合评分: [{score_color} bold]{report.score}[/] 分\n"
                f"💡 操作建议: [{score_color}]{report.advice}[/]",
                title="📊 分析摘要",
                border_style="blue",
            )

            # 信号面板
            signal_panel = Panel(
                f"{bull_text}\n\n{bear_text}", title="⚡ 交易信号", border_style="white"
            )

            console = Console()
            console.print("\n")
            console.print(summary_panel)
            console.print(table)
            console.print(signal_panel)
