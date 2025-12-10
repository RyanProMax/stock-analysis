from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import asdict

from ..env import is_development
from .data_loader import DataLoader
from .model import AnalysisReport
from .factors import MultiFactorAnalyzer
from .console_report import console_report
from .cache_util import CacheUtil

CACHE: Dict[str, AnalysisReport | None] = {}


def _build_cache_key(symbol: str) -> str:
    return f"{datetime.now().strftime('%Y-%m-%d')}_{symbol.upper()}"


def _analyze_symbol(symbol: str, refresh: bool = False) -> Optional[AnalysisReport]:
    try:
        cache_key = _build_cache_key(symbol)

        # 检查内存缓存
        if not refresh and cache_key in CACHE and CACHE[cache_key] is not None:
            print(f"✓ 从内存加载分析报告: {symbol}")
            return CACHE[cache_key]

        # 检查文件缓存
        if not refresh:
            cached_report_dict = CacheUtil.load_report(symbol)
            if cached_report_dict is not None:
                # 将字典转换回 AnalysisReport 对象
                try:
                    from .model import FearGreed, FactorDetail

                    # 重建 FearGreed 对象
                    fear_greed_data = cached_report_dict.get("fear_greed", {})
                    fear_greed = FearGreed(
                        index=fear_greed_data.get("index", 50.0),
                        label=fear_greed_data.get("label", "中性"),
                    )

                    # 重建 FactorDetail 列表
                    def rebuild_factor_list(factors_data):
                        return [
                            FactorDetail(
                                key=f.get("key", ""),
                                name=f.get("name", ""),
                                status=f.get("status", ""),
                                bullish_signals=f.get("bullish_signals", []),
                                bearish_signals=f.get("bearish_signals", []),
                            )
                            for f in factors_data
                        ]

                    report = AnalysisReport(
                        symbol=cached_report_dict.get("symbol", symbol),
                        stock_name=cached_report_dict.get("stock_name", ""),
                        price=cached_report_dict.get("price", 0.0),
                        fear_greed=fear_greed,
                        technical_factors=rebuild_factor_list(
                            cached_report_dict.get("technical_factors", [])
                        ),
                        fundamental_factors=rebuild_factor_list(
                            cached_report_dict.get("fundamental_factors", [])
                        ),
                        qlib_factors=rebuild_factor_list(
                            cached_report_dict.get("qlib_factors", [])
                        ),
                    )

                    # 更新内存缓存
                    CACHE[cache_key] = report
                    return report
                except Exception as e:
                    print(f"⚠️ 从文件缓存重建分析报告失败: {e}")

        print(f"Update Data: {symbol}")
        df, stock_name = DataLoader.get_stock_daily(symbol)
        if df is None or df.empty:
            CACHE[cache_key] = None
            return None

        analyzer = MultiFactorAnalyzer(df, symbol, stock_name)
        report = analyzer.analyze()
        CACHE[cache_key] = report

        # 保存到文件缓存（如果 refresh=True 则强制覆盖）
        if report is not None:
            report_dict = asdict(report)
            CacheUtil.save_report(symbol, report_dict, force=refresh)

        if report is not None and is_development():
            console_report(report)

        return report
    except Exception as e:
        import traceback

        print(f"Error in analysis service for symbol {symbol}: {e}")
        print("完整错误堆栈:")
        traceback.print_exc()
        CACHE[_build_cache_key(symbol)] = None
        return None


def run_stock_analysis(symbol: str, refresh: bool = False) -> Optional[AnalysisReport]:
    """
    保留原有的单只股票分析接口，供内部调用或向后兼容。
    """
    return _analyze_symbol(symbol, refresh)


def run_batch_stock_analysis(symbols: List[str], refresh: bool = False) -> List[AnalysisReport]:
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
