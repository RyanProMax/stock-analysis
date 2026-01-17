"""
服务层 - 报告服务编排

包含:
- stock_service: 统一的股票服务类
- console_report: 控制台报告输出
"""

from .stock_service import StockService, stock_service
from .console_report import console_report

__all__ = [
    "StockService",
    "stock_service",
    "console_report",
]
