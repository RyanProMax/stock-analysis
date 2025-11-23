from src.data_loader import DataLoader
from src.strategy import StockAnalyzer


def main():
    try:
        stock_symbom = "600519"

        df = DataLoader.get_stock_daily(stock_symbom)

        if df is not None:
            StockAnalyzer(df, stock_symbom).analyze()

    except Exception as e:
        print(f"⚠️ 发生未知错误: {e}")


if __name__ == "__main__":
    main()
