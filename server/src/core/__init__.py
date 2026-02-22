"""
核心层 - 数据模型、基础设施和流程编排

包含:
- 数据模型定义 (FactorDetail, AnalysisReport 等)
- 配置常量
- 流程编排 (pipeline)
"""

from .models import (
    FactorDetail,
    FactorAnalysis,
    FearGreed,
    AnalysisReport,
    FactorSignal,
)
from .constants import Config
from .pipeline import StockService, stock_service

__all__ = [
    "FactorDetail",
    "FactorAnalysis",
    "FearGreed",
    "AnalysisReport",
    "FactorSignal",
    "Config",
    "StockService",
    "stock_service",
]
