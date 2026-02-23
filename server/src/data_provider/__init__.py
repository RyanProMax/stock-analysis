"""
数据提供层 - 数据获取、格式处理

包含:
- sources: 数据源（Efinance, Tushare, AkShare, Pytdx, Baostock, yfinance, NASDAQ）
- manager: 数据源管理器（统一调度 + 熔断）
- models: 日线数据模型（DailyData）
- realtime_types: 实时行情/筹码分布模型（预留）
- stock_list: 股票列表服务
"""

from .manager import DataManager
from .stock_list import StockListService
from ..model.data_provider import DailyData, DailyDataCollection
from .realtime_types import UnifiedRealtimeQuote, ChipDistribution, RealtimeSource
from .sources import (
    EfinanceDataSource,
    TushareDataSource,
    AkShareDataSource,
    PytdxDataSource,
    BaostockDataSource,
    YfinanceDataSource,
)

# 创建全局 DataManager 实例
# A股优先级: Efinance(P0) -> Tushare(P1) -> AkShare(P2) -> Pytdx(P2) -> Baostock(P3)
# 美股优先级: yfinance(P0) -> AkShare(P1)
_data_manager = DataManager.create_market_manager(
    cn_fetchers=[
        EfinanceDataSource.get_instance(),
        TushareDataSource.get_instance(),
        AkShareDataSource.get_instance(),
        PytdxDataSource.get_instance(),
        BaostockDataSource.get_instance(),
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
    "DailyData",
    "DailyDataCollection",
    "UnifiedRealtimeQuote",
    "ChipDistribution",
    "RealtimeSource",
]
