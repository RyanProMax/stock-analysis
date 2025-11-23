from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.progress import Progress, BarColumn, TextColumn

from .model import AnalysisReport


def print_report(report: AnalysisReport):
    console = Console()

    if report.data_and_indicators is None or report.data_and_indicators.empty:
        console.print("[bold red]错误：数据为空。[/]")
        return

    last = report.data_and_indicators.iloc[-1]

    # 贪恐指数仪表盘
    # 颜色逻辑：低(恐慌)=绿色机会，高(贪婪)=红色风险
    fg_color = (
        "green"
        if report.fear_greed_index < 40
        else ("red" if report.fear_greed_index > 60 else "yellow")
    )

    fg_bar = Progress(
        TextColumn("[bold]情绪仪表盘[/]"),
        BarColumn(bar_width=None, complete_style=fg_color),
        TextColumn(
            f"[{fg_color}]{report.fear_greed_index:.1f} ({report.fear_greed_label})"
        ),
        expand=True,
    )
    fg_bar.add_task("sentiment", total=100, completed=int(report.fear_greed_index))

    fg_panel = Panel(
        fg_bar,
        title="🧠 市场心理 (Fear & Greed)",
        border_style="white",
        padding=(0, 2),
    )

    # 表格构建
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold white on blue")
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

    # 面板构建
    score_color = (
        "red" if report.score < 40 else ("green" if report.score > 70 else "yellow")
    )
    bull_txt = (
        "\n".join([f"[green]✅ {s}[/]" for s in report.bullish_signals])
        or "[dim]无明显多头信号[/]"
    )
    bear_txt = (
        "\n".join([f"[red]❌ {s}[/]" for s in report.bearish_signals])
        or "[dim]无明显空头信号[/]"
    )

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

    # 输出
    console.print("\n")
    console.print(
        f"[bold underline]🔍 股票分析报告: {report.stock_name} ({report.symbol})[/]\n"
    )
    console.print(fg_panel)  # 优先显示情绪面板
    console.print(table)
    from rich.columns import Columns

    console.print(Columns([left_panel, right_panel]))
