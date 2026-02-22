"""
数据提供层 - 数据获取、格式处理

包含:
- sources: 数据源（Tushare, AkShare, NASDAQ, yfinance）
- manager: 数据源管理器（统一调度 + 熔断）
- stock_list: 股票列表服务
"""

from .manager import DataManager
from .stock_list import StockListService
from .sources import TushareDataSource, AkShareDataSource, YfinanceDataSource

# 创建全局 DataManager 实例
# A股: Tushare -> AkShare
# 美股: yfinance -> AkShare
_data_manager = DataManager.create_market_manager(
    cn_fetchers=[
        TushareDataSource.get_instance(),
        AkShareDataSource.get_instance(),
    ],
    us_fetchers=[
        YfinanceDataSource.get_instance(),
        AkShareDataSource.get_instance(),
    ],
)

# 提供全局访问
data_manager = _data_manager

__all__ = [
    "DataManager",
    "data_manager",
    "StockListService",
]
