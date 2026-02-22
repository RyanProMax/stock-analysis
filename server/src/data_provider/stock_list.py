"""
股票列表服务

提供获取A股和美股股票列表的功能
- A股：支持 Tushare 和 AkShare 两种数据源
- 美股：支持 Tushare 和 NASDAQ API 两种数据源
按日缓存，减少请求频率
"""

from typing import List, Dict, Any, Optional

from .sources.tushare import TushareDataSource
from .sources.akshare import AkShareDataSource
from .sources.nasdaq import NasdaqDataSource


class StockListService:
    """股票列表服务类"""

    # 数据源实例（单例）
    _tushare_source = TushareDataSource.get_instance()
    _akshare_source = AkShareDataSource.get_instance()
    _nasdaq_source = NasdaqDataSource.get_instance()

    # A股数据源优先级
    _a_stock_sources = [_tushare_source, _akshare_source]
    # 美股数据源优先级
    _us_stock_sources = [_nasdaq_source, _tushare_source]

    @classmethod
    def _get_cached(cls, market: str) -> Optional[List[Dict[str, Any]]]:
        """从所有数据源获取缓存"""
        from ..storage import CacheUtil

        # 检查内存缓存
        for source in cls._a_stock_sources + cls._us_stock_sources:
            if source.is_cache_valid(market):
                return source._cache[market]

        # 检查文件缓存
        return CacheUtil.load_stock_list(market)

    @classmethod
    def get_a_stock_list(
        cls, use_tushare: bool = True, refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        获取A股股票列表

        Args:
            use_tushare: 是否优先使用 Tushare（更准确），如果不可用则回退到 AkShare
            refresh: 是否强制刷新缓存

        Returns:
            股票列表，按标准格式返回
        """
        market = "A股"

        # 检查缓存
        if not refresh:
            cached = cls._get_cached(market)
            if cached is not None:
                print(f"✓ 使用缓存的A股列表，共 {len(cached)} 只股票")
                return cached

        # 按优先级尝试数据源
        sources = cls._a_stock_sources if use_tushare else [cls._akshare_source]

        for source in sources:
            if not source.is_available(market):
                continue

            stocks = source.get_a_stocks(refresh=refresh)
            if stocks:
                return stocks

        print("⚠️ 所有A股数据源都失败")
        return []

    @classmethod
    def get_us_stock_list(
        cls, use_tushare: bool = True, refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        获取美股股票列表

        Args:
            use_tushare: 是否允许使用 Tushare 作为兜底（优先使用 NASDAQ API）
            refresh: 是否强制刷新缓存

        Returns:
            股票列表，按标准格式返回
        """
        market = "美股"

        # 检查缓存
        if not refresh:
            cached = cls._get_cached(market)
            if cached is not None:
                print(f"✓ 使用缓存的美股列表，共 {len(cached)} 只股票")
                return cached

        # 按优先级尝试数据源
        sources = cls._us_stock_sources if use_tushare else [cls._nasdaq_source]

        for source in sources:
            if not source.is_available(market):
                continue

            stocks = source.get_us_stocks(refresh=refresh)
            if stocks:
                return stocks

        print("⚠️ 所有美股数据源都失败")
        return []

    @classmethod
    def get_all_stock_list(cls) -> List[Dict[str, Any]]:
        """
        获取所有股票列表（A股 + 美股）

        Returns:
            股票列表，按标准格式返回
        """
        a_stocks = cls.get_a_stock_list()
        us_stocks = cls.get_us_stock_list()
        return a_stocks + us_stocks

    @classmethod
    def search_stocks(cls, keyword: str, market: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        搜索股票（从缓存列表中搜索）

        Args:
            keyword: 搜索关键词（可以是代码或名称）
            market: 市场类型（"A股" 或 "美股"），如果为 None 则搜索所有市场

        Returns:
            匹配的股票列表
        """
        keyword = keyword.upper().strip()
        if not keyword:
            return []

        # 从缓存中获取股票列表
        if market == "A股":
            all_stocks = cls.get_a_stock_list()
        elif market == "美股":
            all_stocks = cls.get_us_stock_list()
        else:
            all_stocks = cls.get_all_stock_list()

        # 搜索匹配
        results = []
        for stock in all_stocks:
            ts_code = str(stock.get("ts_code", "")).upper()
            symbol = str(stock.get("symbol", "")).upper()
            name = str(stock.get("name", "")).upper()
            if keyword in ts_code or keyword in symbol or keyword in name:
                results.append(stock)

        return results
