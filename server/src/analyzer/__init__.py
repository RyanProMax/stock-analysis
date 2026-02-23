# 因子模块统一导出入口
from .base import BaseFactor, FactorLibrary
from .technical_factors import TechnicalFactorLibrary
from .fundamental_factors import FundamentalFactorLibrary
from .qlib_158_factors import Qlib158FactorLibrary
from .multi_factor import MultiFactorAnalyzer
from .trend_analyzer import StockTrendAnalyzer, analyze_stock
from .trend_models import (
    TrendAnalysisResult,
    TrendStatus,
    VolumeStatus,
    BuySignal,
    MACDStatus,
    RSIStatus,
)

__all__ = [
    "BaseFactor",
    "FactorLibrary",
    "TechnicalFactorLibrary",
    "FundamentalFactorLibrary",
    "Qlib158FactorLibrary",
    "MultiFactorAnalyzer",
    # 趋势分析
    "StockTrendAnalyzer",
    "analyze_stock",
    "TrendAnalysisResult",
    "TrendStatus",
    "VolumeStatus",
    "BuySignal",
    "MACDStatus",
    "RSIStatus",
]
