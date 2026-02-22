from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.progress import Progress, BarColumn, TextColumn

from ..core import AnalysisReport


def console_report(report: AnalysisReport):
    console = Console()

    # 贪恐指数仪表盘
    # 颜色逻辑：低(恐慌)=绿色机会，高(贪婪)=红色风险
    fg_color = (
        "green"
        if report.fear_greed.index < 40
        else ("red" if report.fear_greed.index > 60 else "yellow")
    )

    fg_bar = Progress(
        TextColumn("[bold]情绪仪表盘[/]"),
        BarColumn(bar_width=None, complete_style=fg_color),
        TextColumn(f"[{fg_color}]{report.fear_greed.index:.1f} ({report.fear_greed.label})"),
        expand=True,
    )
    fg_bar.add_task("sentiment", total=100, completed=int(report.fear_greed.index))

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
        "",
    )
    table.add_section()

    # 处理信号格式（信号现在是字符串）
    def format_signal(signal):
        return str(signal)

    # 直接使用报告中的分类因子
    technical_factors = report.technical.factors
    fundamental_factors = report.fundamental.factors
    qlib_factors = report.qlib.factors

    # 构建因子详情面板
    factor_panels = []

    # 技术面因子
    if technical_factors:
        tech_content = []
        for factor in technical_factors:
            tech_content.append(f"\n[bold cyan]{factor.name}[/]")
            tech_content.append(f"状态: {factor.status}")
            if factor.bullish_signals:
                tech_content.append("\n[green]多头信号:[/]")
                for sig in factor.bullish_signals:
                    tech_content.append(f"  ✅ {format_signal(sig)}")
            if factor.bearish_signals:
                tech_content.append("\n[red]空头信号:[/]")
                for sig in factor.bearish_signals:
                    tech_content.append(f"  ❌ {format_signal(sig)}")
            tech_content.append("")

        tech_panel = Panel(
            "\n".join(tech_content),
            title="📊 技术面因子",
            border_style="cyan",
        )
        factor_panels.append(tech_panel)

    # 基本面因子
    if fundamental_factors:
        fund_content = []
        for factor in fundamental_factors:
            fund_content.append(f"\n[bold yellow]{factor.name}[/]")
            fund_content.append(f"状态: {factor.status}")
            if factor.bullish_signals:
                fund_content.append("\n[green]多头信号:[/]")
                for sig in factor.bullish_signals:
                    fund_content.append(f"  ✅ {format_signal(sig)}")
            if factor.bearish_signals:
                fund_content.append("\n[red]空头信号:[/]")
                for sig in factor.bearish_signals:
                    fund_content.append(f"  ❌ {format_signal(sig)}")
            fund_content.append("")

        fund_panel = Panel(
            "\n".join(fund_content),
            title="💼 基本面因子",
            border_style="yellow",
        )
        factor_panels.append(fund_panel)

    # Qlib 因子
    if qlib_factors:
        qlib_content = []
        for factor in qlib_factors:
            qlib_content.append(f"\n[bold magenta]{factor.name}[/]")
            qlib_content.append(f"状态: {factor.status}")
            if factor.bullish_signals:
                qlib_content.append("\n[green]多头信号:[/]")
                for sig in factor.bullish_signals:
                    qlib_content.append(f"  ✅ {format_signal(sig)}")
            if factor.bearish_signals:
                qlib_content.append("\n[red]空头信号:[/]")
                for sig in factor.bearish_signals:
                    qlib_content.append(f"  ❌ {format_signal(sig)}")
            qlib_content.append("")

        qlib_panel = Panel(
            "\n".join(qlib_content),
            title="📈 Qlib 因子",
            border_style="magenta",
        )
        factor_panels.append(qlib_panel)

    # 汇总所有因子的信号
    all_bull_signals = []
    all_bear_signals = []
    for factor in technical_factors + fundamental_factors + qlib_factors:
        all_bull_signals.extend(factor.bullish_signals)
        all_bear_signals.extend(factor.bearish_signals)

    bull_txt = (
        "\n".join([f"[green]✅ {format_signal(s)}[/]" for s in all_bull_signals])
        or "[dim]无明显多头信号[/]"
    )
    bear_txt = (
        "\n".join([f"[red]❌ {format_signal(s)}[/]" for s in all_bear_signals])
        or "[dim]无明显空头信号[/]"
    )

    signal_panel = Panel(
        f"{bull_txt}\n\n[white dim]---[/]\n\n{bear_txt}",
        title="⚡ 汇总信号",
        border_style="white",
    )

    # 输出
    console.print("\n")
    console.print(f"[bold underline]🔍 股票分析报告: {report.stock_name} ({report.symbol})[/]\n")
    console.print(fg_panel)  # 优先显示情绪面板
    console.print(table)

    from rich.columns import Columns

    # 显示因子详情
    if factor_panels:
        console.print("\n")
        console.print(Columns(factor_panels))

    # 显示汇总信号
    console.print("\n")
    console.print(signal_panel)
