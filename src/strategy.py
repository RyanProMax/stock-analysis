from stockstats import StockDataFrame
import pandas as pd
from dataclasses import dataclass, field
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from typing import List, Optional


class Config:
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70

    KDJ_J_OVERSOLD = 10
    KDJ_J_OVERBOUGHT = 90

    STRONG_BUY_SCORE = 80
    BUY_SCORE = 60
    NEUTRAL_SCORE = 40
    STRONG_SELL_SCORE = 20


cfg = Config()


@dataclass
class AnalysisReport:
    """封装单次完整的股票分析结果"""

    symbol: str
    price: float
    score: int
    advice: str
    trend_status: str  # 新增：趋势状态 (如：多头排列/空头排列)
    stop_loss_price: float  # 新增：建议止损价
    data_and_indicators: Optional[pd.DataFrame]
    bullish_signals: List[str] = field(default_factory=list)
    bearish_signals: List[str] = field(default_factory=list)


class StockAnalyzer:
    # 扩充了主流因子：均线、ATR、WR、OBV
    INDICATORS_TO_CALCULATE = [
        "macd",
        "macdh",
        "macds",  # MACD
        "rsi_14",  # RSI
        "kdjk",
        "kdjd",
        "kdjj",  # KDJ
        "boll",
        "boll_ub",
        "boll_lb",  # Bollinger
        "close_5_sma",
        "close_10_sma",
        "close_20_sma",
        "close_60_sma",  # 均线系统
        "vr",  # 量比 (Volume Ratio)
        "wr_14",  # 威廉指标 (Williams %R)
        "atr",  # ATR (用于止损)
        "volume",  # 成交量
    ]

    def __init__(self, df: pd.DataFrame, symbol: str, stock_name: str):
        self.raw_df = df
        self.symbol = symbol
        self.stock_name = stock_name
        self.stock = StockDataFrame.retype(df.copy())

        # 计算指标
        for indicator in self.INDICATORS_TO_CALCULATE:
            self.stock.get(indicator)

    def analyze(self) -> AnalysisReport | None:
        """执行多因子加权分析"""
        # 获取最后一行 (最新数据)
        last_row = self.stock.iloc[-1]

        # 获取前一天数据 (用于比较变化，如金叉死叉)
        prev_row = self.stock.iloc[-2] if len(self.stock) > 1 else last_row

        close = float(last_row.get("close", 0.0))
        if close == 0.0:
            return None

        # --- 提取因子 ---
        macd_h = last_row.get("macdh", 0.0)
        rsi = last_row.get("rsi_14", 50.0)
        k, d, j = (
            last_row.get("kdjk", 50),
            last_row.get("kdjd", 50),
            last_row.get("kdjj", 50),
        )
        wr = last_row.get("wr_14", -50.0)  # WR通常是 -100 到 0

        # 均线
        ma5 = last_row.get("close_5_sma", 0)
        ma20 = last_row.get("close_20_sma", 0)
        ma60 = last_row.get("close_60_sma", 0)

        # 波动率
        atr = last_row.get("atr", 0)

        # --- 核心策略逻辑 (加权打分制) ---
        score = 50  # 基础分 50
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
            if macd_h > prev_row.get("macdh", 0):  # 红柱增长
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
        boll_lb = last_row.get("boll_lb", 0)
        boll_ub = last_row.get("boll_ub", 0)
        if close <= boll_lb * 1.01:  # 接近下轨
            score += 10
            bull_signals.append("股价触及布林下轨，支撑较强")
        elif close >= boll_ub * 0.99:
            score -= 10
            bear_signals.append("股价触及布林上轨，压力较大")

        # 4. 风险风控计算 (ATR)
        # 建议止损价 = 当前价 - 2倍ATR (常规波动范围之外)
        stop_loss = close - (2 * atr) if atr > 0 else close * 0.95

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

        # 限制 Score 范围 0-100
        score = max(0, min(100, score))

        # 构建最终 DataFrame
        final_cols = [
            c
            for c in ["open", "close", "high", "low", "volume"]
            + self.INDICATORS_TO_CALCULATE
            if c in self.stock.columns
        ]

        report = AnalysisReport(
            symbol=self.symbol,
            price=close,
            score=score,
            advice=advice,
            trend_status=trend_status,
            stop_loss_price=stop_loss,
            data_and_indicators=self.stock[final_cols],
            bullish_signals=bull_signals,
            bearish_signals=bear_signals,
        )

        self.print_report(report)
        return report

    def print_report(self, report: AnalysisReport):
        console = Console()

        if report.data_and_indicators is None or report.data_and_indicators.empty:
            console.print("[bold red]错误：数据为空。[/]")
            return

        last = report.data_and_indicators.iloc[-1]

        # --- 1. 表格构建 ---
        table = Table(
            box=box.ROUNDED, show_header=True, header_style="bold white on blue"
        )
        table.add_column("维度", style="dim")
        table.add_column("指标", style="bold cyan")
        table.add_column("数值", justify="right")
        table.add_column("状态分析", justify="left")

        # 基础数据
        table.add_row(
            "基础",
            "最新价格",
            f"¥ {report.price:.2f}",
            f"[bold]{report.trend_status}[/]",
        )
        table.add_row(
            "基础",
            "建议止损",
            f"¥ {report.stop_loss_price:.2f}",
            "[italic red]跌破此位离场[/]",
        )
        table.add_section()

        # 趋势
        ma5, ma20 = last.get("close_5_sma", 0), last.get("close_20_sma", 0)
        ma_gap = (ma5 - ma20) / ma20 * 100
        table.add_row(
            "趋势",
            "MA5 vs MA20",
            f"{ma_gap:+.2f}%",
            "[green]金叉发散[/]" if ma5 > ma20 else "[red]空头压制[/]",
        )

        # 动能
        rsi = last.get("rsi_14", 50)
        rsi_style = (
            "[red]超买[/]" if rsi > 70 else ("[green]超卖[/]" if rsi < 30 else "中性")
        )
        table.add_row("动能", "RSI (14)", f"{rsi:.1f}", rsi_style)

        macd = last.get("macdh", 0)
        macd_style = "[red]空头力度[/]" if macd < 0 else "[green]多头力度[/]"
        table.add_row("动能", "MACD 柱", f"{macd:.3f}", macd_style)

        wr = last.get("wr_14", -50)
        table.add_row(
            "动能",
            "Williams %R",
            f"{wr:.1f}",
            "[green]底部超卖[/]" if wr < -80 else "正常",
        )

        # 波动
        bb_ub = last.get("boll_ub", 0)
        dist_ub = (bb_ub - report.price) / report.price * 100
        table.add_row("通道", "距布林上轨", f"{dist_ub:.1f}%", "空间越大上涨潜力越大")

        # --- 2. 面板构建 ---
        score_color = (
            "red" if report.score < 40 else ("green" if report.score > 70 else "yellow")
        )

        # 信号文本
        bull_txt = (
            "\n".join([f"[green]✅ {s}[/]" for s in report.bullish_signals])
            or "[dim]无明显多头信号[/]"
        )
        bear_txt = (
            "\n".join([f"[red]❌ {s}[/]" for s in report.bearish_signals])
            or "[dim]无明显空头信号[/]"
        )

        summary_grid = Table.grid(expand=True)
        summary_grid.add_column(ratio=1)
        summary_grid.add_column(ratio=1)

        # 左侧：综合评分
        left_panel = Panel(
            f"\n[bold {score_color} reverse]  {report.score} 分  [/]\n\n"
            f"建议: [bold {score_color}]{report.advice}[/]\n"
            f"趋势: {report.trend_status}",
            title="🎯 综合评级",
            border_style=score_color,
        )

        # 右侧：信号详情
        right_panel = Panel(
            f"{bull_txt}\n\n[white dim]---[/]\n\n{bear_txt}",
            title="⚡ 信号侦测",
            border_style="white",
        )

        # --- 3. 输出 ---
        console.print("\n")
        console.print(
            f"[bold underline]🔍 深度股票分析报告: {self.stock_name} ({self.symbol})[/]"
        )
        console.print(table)

        from rich.columns import Columns

        console.print(Columns([left_panel, right_panel]))
