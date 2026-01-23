"""
核心数据模型定义

包含所有业务实体的数据类定义��
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class FactorDetail:
    """因子详情"""

    key: str  # 因子类型标识：trend/volatility/momentum/volume/fundamental
    name: str  # 因子名称
    status: str  # 因子状态描述
    bullish_signals: List[str] = field(default_factory=list)
    bearish_signals: List[str] = field(default_factory=list)
    data_source: str = ""  # 数据源标识


@dataclass
class FactorAnalysis:
    """因子分析结果（技术面/基本面/Qlib）"""

    factors: List[FactorDetail] = field(default_factory=list)
    data_source: str = ""
    raw_data: Dict[str, Any] | None = None


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
    # 行业信息（用于基本面分析时的行业对比）
    industry: str = ""
    # 因子分析结果（新结构）
    technical: FactorAnalysis = field(default_factory=FactorAnalysis)
    fundamental: FactorAnalysis = field(default_factory=FactorAnalysis)
    qlib: FactorAnalysis = field(default_factory=FactorAnalysis)


@dataclass
class FactorSignal:
    """因子信号"""

    key: str
    name: str
    signal: str  # bullish/bearish/neutral
    strength: float  # 信号强度 0-1
    reason: str  # 信号原因
