"""
统一的股票服务类

提供股票数据的统一接口，包括：
- 股票列表服务
- 基础数据获取
- 基本面分析
- 技术面分析
- Qlib因子分析
- 缓存管理
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import asdict
import pandas as pd

from ..data import DataLoader, StockListService, CacheUtil
from ..indicators import MultiFactorAnalyzer
from ..core import AnalysisReport, FactorDetail, FearGreed
from ..env import is_development


class StockService:
    """统一的股票服务类，封装所有股票相关操作"""

    def __init__(self):
        """初始化服务"""
        self.cache = {}  # 内存缓存

    def _build_cache_key(self, symbol: str) -> str:
        """构建缓存键"""
        return f"{CacheUtil.get_cst_date_key()}_{symbol.upper()}"

    # ==================== 基础数据获取 ====================

    def get_stock_data(self, symbol: str) -> Tuple[Optional[pd.DataFrame], str, str]:
        """
        获取股票日线数据

        Args:
            symbol: 股票代码

        Returns:
            (DataFrame, stock_name, data_source): 数据、股票名称和数据源，失败时返回 (None, symbol, "")
        """
        return DataLoader.get_stock_daily(symbol)

    def get_financial_data(self, symbol: str) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        获取财务数据

        Args:
            symbol: 股票代码

        Returns:
            (财务数据字典, 数据源): 包含PE、PB、ROE等指标
        """
        return DataLoader.get_financial_data(symbol)

    # ==================== 股票列表服务 ====================

    def get_stock_list(
        self, market: Optional[str] = None, refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        获取股票列表

        Args:
            market: 市场类型 ('A股', '美股', None表示全部)
            refresh: 是否强制刷新缓存

        Returns:
            股票列表
        """
        if market == "A股":
            return StockListService.get_a_stock_list(refresh=refresh)
        elif market == "美股":
            return StockListService.get_us_stock_list(refresh=refresh)
        else:
            return StockListService.get_all_stock_list()

    def search_stocks(self, keyword: str, market: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        搜索股票

        Args:
            keyword: 搜索关键词
            market: 市场类型

        Returns:
            匹配的股票列表
        """
        return StockListService.search_stocks(keyword, market)

    # ==================== 分析服务 ====================

    def analyze_symbol(
        self, symbol: str, refresh: bool = False, include_qlib_factors: bool = False
    ) -> Optional[AnalysisReport]:
        """
        分析单只股票

        Args:
            symbol: 股票代码
            refresh: 是否强制刷新缓存
            include_qlib_factors: 是否包含 Qlib 158 因子，默认 False

        Returns:
            分析报告
        """
        try:
            cache_key = self._build_cache_key(symbol)

            # 检查内存缓存
            if not refresh and cache_key in self.cache and self.cache[cache_key] is not None:
                print(f"✓ 从内存加载分析报告: {symbol}")
                return self.cache[cache_key]

            # 检查文件缓存
            if not refresh:
                cached_report_dict = CacheUtil.load_report(symbol)
                if cached_report_dict is not None:
                    report = self._rebuild_report_from_dict(cached_report_dict, symbol)
                    if report:
                        self.cache[cache_key] = report
                        return report

            # 执行分析
            print(f"Update Data: {symbol}")
            df, stock_name, data_source = self.get_stock_data(symbol)
            if df is None or df.empty:
                self.cache[cache_key] = None
                return None

            # 获取财务数据源
            _, financial_data_source = self.get_financial_data(symbol)

            analyzer = MultiFactorAnalyzer(
                df,
                symbol,
                stock_name,
                include_qlib_factors=include_qlib_factors,
                data_source=data_source,
                financial_data_source=financial_data_source,
            )
            report = analyzer.analyze()
            self.cache[cache_key] = report

            # 保存到文件缓存
            if report is not None:
                report_dict = asdict(report)
                CacheUtil.save_report(symbol, report_dict, force=refresh)

            # 开发环境输出控制台报告
            if report is not None and is_development():
                from .console_report import console_report

                console_report(report)

            return report

        except Exception as e:
            import traceback

            print(f"Error in analysis service for symbol {symbol}: {e}")
            print("完整错误堆栈:")
            traceback.print_exc()
            self.cache[self._build_cache_key(symbol)] = None
            return None

    def batch_analyze(
        self, symbols: List[str], refresh: bool = False, include_qlib_factors: bool = False
    ) -> List[AnalysisReport]:
        """
        批量分析股票

        Args:
            symbols: 股票代码列表
            refresh: 是否强制刷新缓存
            include_qlib_factors: 是否包含 Qlib 158 因子，默认 False

        Returns:
            成功分析的报告列表
        """
        reports: List[AnalysisReport] = []
        seen: set[str] = set()

        for symbol in symbols:
            normalized = symbol.upper()
            if normalized in seen:
                continue
            seen.add(normalized)
            report = self.analyze_symbol(normalized, refresh, include_qlib_factors)
            if report is not None:
                reports.append(report)

        return reports

    # ==================== 因子分析服务 ====================

    def get_fundamental_factors(self, symbol: str) -> Optional[List[FactorDetail]]:
        """
        获取基本面因子

        Args:
            symbol: 股票代码

        Returns:
            基本面因子列表
        """
        report = self.analyze_symbol(symbol)
        return report.fundamental_factors if report else None

    def get_technical_factors(self, symbol: str) -> Optional[List[FactorDetail]]:
        """
        获取技术面因子

        Args:
            symbol: 股票代码

        Returns:
            技术面因子列表
        """
        report = self.analyze_symbol(symbol)
        return report.technical_factors if report else None

    def get_qlib_factors(self, symbol: str) -> Optional[List[FactorDetail]]:
        """
        获取Qlib因子

        Args:
            symbol: 股票代码

        Returns:
            Qlib因子列表
        """
        report = self.analyze_symbol(symbol)
        return report.qlib_factors if report else None

    # ==================== 辅助方法 ====================

    def _rebuild_report_from_dict(
        self, report_dict: Dict[str, Any], symbol: str
    ) -> Optional[AnalysisReport]:
        """
        从字典重建分析报告

        Args:
            report_dict: 报告字典
            symbol: 股票代码

        Returns:
            分析报告对象
        """
        try:
            # 重建 FearGreed 对象
            fear_greed_data = report_dict.get("fear_greed", {})
            fear_greed = FearGreed(
                index=fear_greed_data.get("index", 50.0),
                label=fear_greed_data.get("label", "中性"),
            )

            # 重建 FactorDetail 列表的辅助函数
            def rebuild_factor_list(factors_data):
                return [
                    FactorDetail(
                        key=f.get("key", ""),
                        name=f.get("name", ""),
                        status=f.get("status", ""),
                        bullish_signals=f.get("bullish_signals", []),
                        bearish_signals=f.get("bearish_signals", []),
                        raw_data=f.get("raw_data"),
                        data_source=f.get("data_source", ""),
                    )
                    for f in factors_data
                ]

            # 重建报告
            report = AnalysisReport(
                symbol=report_dict.get("symbol", symbol),
                stock_name=report_dict.get("stock_name", ""),
                price=report_dict.get("price", 0.0),
                fear_greed=fear_greed,
                industry=report_dict.get("industry", ""),
                data_source=report_dict.get("data_source", ""),
                financial_data_source=report_dict.get("financial_data_source", ""),
                technical_factors=rebuild_factor_list(report_dict.get("technical_factors", [])),
                fundamental_factors=rebuild_factor_list(report_dict.get("fundamental_factors", [])),
                qlib_factors=rebuild_factor_list(report_dict.get("qlib_factors", [])),
                technical_raw_data=report_dict.get("technical_raw_data"),
                fundamental_raw_data=report_dict.get("fundamental_raw_data"),
            )

            return report

        except Exception as e:
            print(f"⚠️ 从文件缓存重建分析报告失败: {e}")
            return None

    # ==================== Agent专用接口 ====================

    def get_analysis_data_for_agent(self, symbol: str) -> Dict[str, Any]:
        """
        获取分析数据（供Agent使用）

        Args:
            symbol: 股票代码

        Returns:
            包含基础信息的字典
        """
        try:
            df, stock_name, data_source = self.get_stock_data(symbol)
            if df is None or df.empty:
                return {"success": False, "error": f"无法获取股票 {symbol} 的数据"}

            # 获取最新数据
            latest_data = df.iloc[-1]

            # 获取财务数据
            financial_data, financial_data_source = self.get_financial_data(symbol)

            return {
                "success": True,
                "data": {
                    "basic_info": {
                        "symbol": symbol,
                        "name": stock_name,
                        "price": latest_data.get("close", 0),
                        "change": latest_data.get("change", 0),
                        "change_pct": latest_data.get("change_pct", 0),
                        "data_source": data_source,
                        "financial_data_source": financial_data_source,
                    },
                    "stock_data": df.to_dict("records"),
                    "financial_data": financial_data or {},
                },
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_fundamental_factors_for_agent(self, symbol: str) -> Dict[str, Any]:
        """获取基本面因子（供Agent使用）"""
        try:
            factors = self.get_fundamental_factors(symbol)
            if factors is None:
                return {
                    "success": False,
                    "error": f"无法获取股票 {symbol} 的基本面分析",
                }
            return {"success": True, "data": factors}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_technical_factors_for_agent(self, symbol: str) -> Dict[str, Any]:
        """获取技术面因子（供Agent使用）"""
        try:
            factors = self.get_technical_factors(symbol)
            if factors is None:
                return {
                    "success": False,
                    "error": f"无法获取股票 {symbol} 的技术面分析",
                }
            return {"success": True, "data": factors}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_qlib_factors_for_agent(self, symbol: str) -> Dict[str, Any]:
        """获取Qlib因子（供Agent使用）"""
        try:
            factors = self.get_qlib_factors(symbol)
            if factors is None:
                return {
                    "success": False,
                    "error": f"无法获取股票 {symbol} 的 Qlib 因子分析",
                }
            return {"success": True, "data": factors}
        except Exception as e:
            return {"success": False, "error": str(e)}


# 创建全局实例
stock_service = StockService()
