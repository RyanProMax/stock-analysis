from .data_loader import DataLoader
from .strategy import StockAnalyzer, AnalysisReport
from typing import Optional

def run_stock_analysis(symbol: str) -> Optional[AnalysisReport]:
    """
    Orchestrates the stock analysis process.
    1. Loads stock data.
    2. Analyzes the data.
    3. Returns the analysis report.
    """
    try:
        [df, stock_name] = DataLoader.get_stock_daily(symbol)
        if df is not None and not df.empty:
            analyzer = StockAnalyzer(df, symbol, stock_name)
            report = analyzer.analyze()
            return report
    except Exception as e:
        print(f"Error in analysis service for symbol {symbol}: {e}")
        return None
