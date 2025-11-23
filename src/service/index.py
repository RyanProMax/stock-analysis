from datetime import datetime

from .data_loader import DataLoader
from .strategy import StockAnalyzer, AnalysisReport

from typing import Optional

CACHE = {}


def run_stock_analysis(symbol: str, refresh: bool = False) -> Optional[AnalysisReport]:
    """
    Orchestrates the stock analysis process.
    1. Loads stock data.
    2. Analyzes the data.
    3. Returns the analysis report.
    """
    try:
        cache_key = f"{datetime.now().strftime("%Y-%m-%d")}_symbol"
        if not refresh and cache_key in CACHE and CACHE[cache_key] is not None:
            return CACHE[cache_key]

        print(f"Update Data: {symbol}")
        [df, stock_name] = DataLoader.get_stock_daily(symbol)
        if df is not None and not df.empty:
            analyzer = StockAnalyzer(df, symbol, stock_name)
            report = analyzer.analyze()
            CACHE[cache_key] = report
            return report
    except Exception as e:
        print(f"Error in analysis service for symbol {symbol}: {e}")
        return None
