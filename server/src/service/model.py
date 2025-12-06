from dataclasses import dataclass, field
from typing import List, Dict, Any


class Config:
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    KDJ_J_OVERSOLD = 10
    KDJ_J_OVERBOUGHT = 90


cfg = Config()


@dataclass
class FactorDetail:
    """因子详情"""

    key: str  # 因子类型标识：trend/volatility/momentum/volume/fundamental
    name: str  # 因子名称
    category: str  # 因子分类：基本面/技术面
    status: str  # 因子状态描述
    bullish_signals: List[Dict[str, Any]] = field(default_factory=list)
    bearish_signals: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class FearGreed:
    """贪恐指数对象"""

    index: float  # 贪恐指数值 (0-100)
    label: str  # 贪恐指数标签


@dataclass
class AnalysisReport:
    """封装单次完整的股票分析结果"""

    symbol: str
    stock_name: str
    price: float
    # 基础指标
    fear_greed: FearGreed = field(default_factory=lambda: FearGreed(index=50.0, label="中性"))
    # 技术面因子
    technical_factors: List[FactorDetail] = field(default_factory=list)
    # 基本面因子
    fundamental_factors: List[FactorDetail] = field(default_factory=list)
    # Qlib 因子
    qlib_factors: List[FactorDetail] = field(default_factory=list)
