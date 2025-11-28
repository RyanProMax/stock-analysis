from datetime import datetime
from typing import Dict, List, Optional

from .data_loader import DataLoader
from .model import AnalysisReport
from .strategy import StockAnalyzer

CACHE: Dict[str, AnalysisReport | None] = {}


def _build_cache_key(symbol: str) -> str:
    return f"{datetime.now().strftime('%Y-%m-%d')}_{symbol.upper()}"


def _analyze_symbol(symbol: str, refresh: bool = False) -> Optional[AnalysisReport]:
    try:
        cache_key = _build_cache_key(symbol)
        if not refresh and cache_key in CACHE and CACHE[cache_key] is not None:
            return CACHE[cache_key]

        print(f"Update Data: {symbol}")
        df, stock_name = DataLoader.get_stock_daily(symbol)
        if df is None or df.empty:
            CACHE[cache_key] = None
            return None

        analyzer = StockAnalyzer(df, symbol, stock_name)
        report = analyzer.analyze()
        CACHE[cache_key] = report
        return report
    except Exception as e:
        print(f"Error in analysis service for symbol {symbol}: {e}")
        CACHE[_build_cache_key(symbol)] = None
        return None


def run_stock_analysis(symbol: str, refresh: bool = False) -> Optional[AnalysisReport]:
    """
    保留原有的单只股票分析接口，供内部调用或向后兼容。
    """
    return _analyze_symbol(symbol, refresh)


def run_batch_stock_analysis(
    symbols: List[str], refresh: bool = False
) -> List[AnalysisReport]:
    """
    批量执行股票分析，自动跳过获取失败的股票，仅返回成功结果。
    """
    reports: List[AnalysisReport] = []
    seen: set[str] = set()

    for symbol in symbols:
        normalized = symbol.upper()
        if normalized in seen:
            continue
        seen.add(normalized)
        report = _analyze_symbol(normalized, refresh)
        if report is not None:
            reports.append(report)

    return reports
