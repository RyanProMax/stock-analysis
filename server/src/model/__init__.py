# -*- coding: utf-8 -*-
"""
数据类型定义模块

包含所有业务实体的数据类定义，独立于其他业务模块，避免循环依赖
"""

from .trend import (
    TrendStatus,
    VolumeStatus,
    BuySignal,
    MACDStatus,
    RSIStatus,
    TrendAnalysisResult,
)

from .report import (
    FactorDetail,
    FactorAnalysis,
    FearGreed,
    AnalysisReport,
    FactorSignal,
)

from .data_provider import (
    DailyData,
    DailyDataCollection,
)

__all__ = [
    # 趋势分析
    "TrendStatus",
    "VolumeStatus",
    "BuySignal",
    "MACDStatus",
    "RSIStatus",
    "TrendAnalysisResult",
    # 报告
    "FactorDetail",
    "FactorAnalysis",
    "FearGreed",
    "AnalysisReport",
    "FactorSignal",
    # 数据提供者
    "DailyData",
    "DailyDataCollection",
]
