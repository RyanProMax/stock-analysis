from src.data_loader import DataLoader
from src.strategy import StockAnalyzer


def print_report(report):
    print("\n" + "=" * 50)
    print(f"📊 股票分析报告: {report.symbol}")
    print("=" * 50)
    print(f"💰 最新价格: {report.price:.2f}")
    print(f"🏆 综合评分: {report.score} 分")
    print(f"💡 操作建议: {report.advice}")

    print("-" * 50)
    print("✅ [利好因素 - 买入理由]")
    if report.bullish_signals:
        for s in report.bullish_signals:
            print(f"   * {s}")
    else:
        print("   (无明显技术面利好)")

    print("-" * 50)
    print("❌ [风险因素 - 卖出理由]")
    if report.bearish_signals:
        for s in report.bearish_signals:
            print(f"   * {s}")
    else:
        print("   (无明显技术面风险)")
    print("=" * 50 + "\n")


def main():
    try:
        stock_symbom = "600519"

        df = DataLoader.get_stock_daily(stock_symbom)

        if df is not None:
            report = StockAnalyzer(df, stock_symbom).analyze()
            print_report(report)

    except Exception as e:
        print(f"⚠️ 发生未知错误: {e}")


if __name__ == "__main__":
    main()
