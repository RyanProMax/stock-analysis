from dataclasses import dataclass, field
import pandas as pd
from typing import List, Optional, Dict, Any


class Config:
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    KDJ_J_OVERSOLD = 10
    KDJ_J_OVERBOUGHT = 90


cfg = Config()


@dataclass
class FactorDetail:
    """因子详情"""

    name: str  # 因子名称
    category: str  # 因子分类：基本面/技术面
    status: str  # 因子状态描述
    bullish_signals: List[Dict[str, Any]] = field(default_factory=list)
    bearish_signals: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AnalysisReport:
    """封装单次完整的股票分析结果"""

    symbol: str
    stock_name: str
    price: float
    trend_status: str
    data_and_indicators: Optional[pd.DataFrame]
    # 各因子详情
    trend_factor: Optional[FactorDetail] = None
    volatility_factor: Optional[FactorDetail] = None
    momentum_factor: Optional[FactorDetail] = None
    volume_factor: Optional[FactorDetail] = None
    fundamental_factor: Optional[FactorDetail] = None
    # 汇总信号
    bullish_signals: List[Dict[str, Any]] = field(default_factory=list)
    bearish_signals: List[Dict[str, Any]] = field(default_factory=list)
    # 基础指标
    fear_greed_index: float = 50.0
    fear_greed_label: str = "中性"
