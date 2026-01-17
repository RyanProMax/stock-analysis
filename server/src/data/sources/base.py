"""
股票数据源基类

定义所有数据源的统一接口和返回格式
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd
import os


class BaseStockDataSource(ABC):
    """股票数据源基类"""

    # 缓存实例
    _instances: Dict[str, "BaseStockDataSource"] = {}

    # 数据源名称
    SOURCE_NAME: str = "base"

    def __init__(self):
        # 内存缓存：{market: [stocks]}
        self._cache: Dict[str, List[Dict[str, Any]]] = {}
        # 缓存日期：{market: date}
        self._cache_date: Dict[str, str] = {}

    @classmethod
    def get_instance(cls) -> "BaseStockDataSource":
        """获取单例实例"""
        if cls.SOURCE_NAME not in cls._instances:
            cls._instances[cls.SOURCE_NAME] = cls()
        return cls._instances[cls.SOURCE_NAME]

    @staticmethod
    def get_cache_key() -> str:
        """获取缓存日期键"""
        from ..cache import CacheUtil

        return CacheUtil.get_cst_date_key()

    def is_cache_valid(self, market: str) -> bool:
        """检查缓存是否有效"""
        today = self.get_cache_key()
        return (
            market in self._cache
            and market in self._cache_date
            and self._cache_date[market] == today
            and len(self._cache[market]) > 0
        )

    def update_cache(self, market: str, stocks: List[Dict[str, Any]]) -> None:
        """更新缓存"""
        from ..cache import CacheUtil

        if len(stocks) > 0:
            self._cache[market] = stocks
            self._cache_date[market] = self.get_cache_key()
            CacheUtil.save_stock_list(market, stocks)

    def get_cached(self, market: str) -> Optional[List[Dict[str, Any]]]:
        """获取缓存数据"""
        if self.is_cache_valid(market):
            return self._cache[market]

        # 尝试从文件缓存加载
        from ..cache import CacheUtil

        cached_data = CacheUtil.load_stock_list(market)
        if cached_data is not None:
            self._cache[market] = cached_data
            self._cache_date[market] = self.get_cache_key()
        return cached_data

    def clear_cache(self, market: str) -> None:
        """清除缓存"""
        if market in self._cache:
            del self._cache[market]
        if market in self._cache_date:
            del self._cache_date[market]

    @staticmethod
    def normalize_dataframe(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        将 DataFrame 标准化为字典列表

        Args:
            df: pandas DataFrame

        Returns:
            标准化的字典列表
        """
        stocks = df.to_dict("records")
        for stock in stocks:
            for key, value in stock.items():
                if pd.isna(value):
                    stock[key] = None
                elif not isinstance(value, (int, float, bool)):
                    stock[key] = str(value)
        return stocks

    @abstractmethod
    def fetch_a_stocks(self) -> List[Dict[str, Any]]:
        """
        获取 A 股股票列表

        Returns:
            标准格式的股票列表，包含以下字段：
            - ts_code: 股票代码（如 000001.SZ）
            - symbol: 股票代码（如 000001）
            - name: 股票名称
            - area: 地区
            - industry: 行业
            - market: 市场类型
            - list_date: 上市日期
        """
        pass

    @abstractmethod
    def fetch_us_stocks(self) -> List[Dict[str, Any]]:
        """
        获取美股股票列表

        Returns:
            标准格式的股票列表
        """
        pass

    def get_a_stocks(self, refresh: bool = False) -> List[Dict[str, Any]]:
        """
        获取 A 股股票列表（带缓存）

        Args:
            refresh: 是否强制刷新缓存

        Returns:
            标准格式的股票列表
        """
        market = "A股"

        if not refresh:
            cached = self.get_cached(market)
            if cached is not None:
                print(
                    f"✓ 使用{self.SOURCE_NAME}缓存的A股列表"
                    f"（{self._cache_date[market]}），共 {len(cached)} 只股票"
                )
                return cached

        try:
            stocks = self.fetch_a_stocks()
            if stocks:
                self.update_cache(market, stocks)
                print(f"✓ 使用 {self.SOURCE_NAME} 获取A股列表，共 {len(stocks)} 只股票（已缓存）")
                return stocks
        except Exception as e:
            print(f"⚠️ {self.SOURCE_NAME} 获取A股列表失败: {type(e).__name__}: {e}")
            self.clear_cache(market)

        return []

    def get_us_stocks(self, refresh: bool = False) -> List[Dict[str, Any]]:
        """
        获取美股股票列表（带缓存）

        Args:
            refresh: 是否强制刷新缓存

        Returns:
            标准格式的股票列表
        """
        market = "美股"

        if not refresh:
            cached = self.get_cached(market)
            if cached is not None:
                print(
                    f"✓ 使用{self.SOURCE_NAME}缓存的美股列表"
                    f"（{self._cache_date[market]}），共 {len(cached)} 只股票"
                )
                return cached

        try:
            stocks = self.fetch_us_stocks()
            if stocks:
                self.update_cache(market, stocks)
                print(f"✓ 使用 {self.SOURCE_NAME} 获取美股列表，共 {len(stocks)} 只股票（已缓存）")
                return stocks
        except Exception as e:
            print(f"⚠️ {self.SOURCE_NAME} 获取美股列表失败: {type(e).__name__}: {e}")
            self.clear_cache(market)

        return []

    @abstractmethod
    def is_available(self, market: str) -> bool:
        """
        检查数据源是否可用于指定市场

        Args:
            market: 市场类型（"A股" 或 "美股"）

        Returns:
            是否可用
        """
        pass
