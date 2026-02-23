"""
实时行情统一类型定义

设计目标：
1. 统一各数据源的实时行情返回结构（对齐 daily_stock_analysis）
2. 为未来实时行情功能预留数据模型
3. 所有模型包含 source 字段，便于调试

注意：
- 当前 stock-analysis 不支持实时行情，这些模型为未来扩展预留
- 未实现的字段在注释中说明
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum


class RealtimeSource(Enum):
    """实时行情数据源"""

    TUSHARE = "tushare"  # Tushare Pro
    AKSHARE = "akshare"  # AkShare
    YFINANCE = "yfinance"  # Yahoo Finance (美股)
    EFINANCE = "efinance"  # 东方财富（A股首选）
    PYTDX = "pytdx"  # 通达信
    BAOSTOCK = "baostock"  # Baostock
    FALLBACK = "fallback"  # 降级兜底


@dataclass
class UnifiedRealtimeQuote:
    """
    统一实时行情数据结构

    设计原则：
    - 各数据源返回的字段可能不同，缺失字段用 None 表示
    - 主流程使用 getattr(quote, field, None) 获取，保证兼容性
    - source 字段标记数据来源，便于调试

    对齐 daily_stock_analysis 的 UnifiedRealtimeQuote
    """

    code: str
    name: str = ""
    source: RealtimeSource = RealtimeSource.FALLBACK

    # === 核心价格数据 ===
    price: Optional[float] = None  # 最新价
    change_pct: Optional[float] = None  # 涨跌幅(%)
    change_amount: Optional[float] = None  # 涨跌额

    # === 量价指标 ===
    volume: Optional[int] = None  # 成交量（手）
    amount: Optional[float] = None  # 成交额（元）
    volume_ratio: Optional[float] = None  # 量比
    turnover_rate: Optional[float] = None  # 换手率(%)
    amplitude: Optional[float] = None  # 振幅(%)

    # === 价格区间 ===
    open_price: Optional[float] = None  # 开盘价
    high: Optional[float] = None  # 最高价
    low: Optional[float] = None  # 最低价
    pre_close: Optional[float] = None  # 昨收价

    # === 估值指标 ===
    # 注：当前 fetcher 未返回这些字段，未来可从 AkShare/Tushare 补充
    pe_ratio: Optional[float] = None  # 市盈率(动态)
    pb_ratio: Optional[float] = None  # 市净率
    total_mv: Optional[float] = None  # 总市值(元)
    circ_mv: Optional[float] = None  # 流通市值(元)

    # === 其他指标 ===
    # 注：当前 fetcher 未返回这些字段
    change_60d: Optional[float] = None  # 60日涨跌幅(%)
    high_52w: Optional[float] = None  # 52周最高
    low_52w: Optional[float] = None  # 52周最低

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（过滤 None 值）"""
        result = {
            "code": self.code,
            "name": self.name,
            "source": self.source.value,
        }
        # 只添加非 None 的字段
        optional_fields = [
            "price",
            "change_pct",
            "change_amount",
            "volume",
            "amount",
            "volume_ratio",
            "turnover_rate",
            "amplitude",
            "open_price",
            "high",
            "low",
            "pre_close",
            "pe_ratio",
            "pb_ratio",
            "total_mv",
            "circ_mv",
            "change_60d",
            "high_52w",
            "low_52w",
        ]
        for f in optional_fields:
            val = getattr(self, f, None)
            if val is not None:
                result[f] = val
        return result

    def has_basic_data(self) -> bool:
        """检查是否有基本的价格数据"""
        return self.price is not None and self.price > 0

    def has_volume_data(self) -> bool:
        """检查是否有量价数据"""
        return self.volume_ratio is not None or self.turnover_rate is not None


@dataclass
class ChipDistribution:
    """
    筹码分布数据

    反映持仓成本分布和获利情况

    对齐 daily_stock_analysis 的 ChipDistribution

    注：当前 stock-analysis 的 fetcher 未实现筹码分布接口
    """

    code: str
    date: str = ""
    source: str = "akshare"

    # 获利情况
    profit_ratio: float = 0.0  # 获利比例(0-1)
    avg_cost: float = 0.0  # 平均成本

    # 筹码集中度
    cost_90_low: float = 0.0  # 90%筹码成本下限
    cost_90_high: float = 0.0  # 90%筹码成本上限
    concentration_90: float = 0.0  # 90%筹码集中度（越小越集中）

    cost_70_low: float = 0.0  # 70%筹码成本下限
    cost_70_high: float = 0.0  # 70%筹码成本上限
    concentration_70: float = 0.0  # 70%筹码集中度

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "code": self.code,
            "date": self.date,
            "source": self.source,
            "profit_ratio": self.profit_ratio,
            "avg_cost": self.avg_cost,
            "cost_90_low": self.cost_90_low,
            "cost_90_high": self.cost_90_high,
            "concentration_90": self.concentration_90,
            "cost_70_low": self.cost_70_low,
            "cost_70_high": self.cost_70_high,
            "concentration_70": self.concentration_70,
        }

    def get_chip_status(self, current_price: float) -> str:
        """
        获取筹码状态描述

        Args:
            current_price: 当前股价

        Returns:
            筹码状态描述
        """
        status_parts = []

        # 获利比例分析
        if self.profit_ratio >= 0.9:
            status_parts.append("获利盘极高(>90%)")
        elif self.profit_ratio >= 0.7:
            status_parts.append("获利盘较高(70-90%)")
        elif self.profit_ratio >= 0.5:
            status_parts.append("获利盘中等(50-70%)")
        elif self.profit_ratio >= 0.3:
            status_parts.append("套牢盘较多(>30%)")
        else:
            status_parts.append("套牢盘极重(>70%)")

        # 筹码集中度分析 (90%集中度 < 10% 表示集中)
        if self.concentration_90 < 0.08:
            status_parts.append("筹码高度集中")
        elif self.concentration_90 < 0.15:
            status_parts.append("筹码较集中")
        elif self.concentration_90 < 0.25:
            status_parts.append("筹码分散度中等")
        else:
            status_parts.append("筹码较分散")

        # 成本与现价关系
        if current_price > 0 and self.avg_cost > 0:
            cost_diff = (current_price - self.avg_cost) / self.avg_cost * 100
            if cost_diff > 20:
                status_parts.append(f"现价高于平均成本{cost_diff:.1f}%")
            elif cost_diff > 5:
                status_parts.append(f"现价略高于成本{cost_diff:.1f}%")
            elif cost_diff > -5:
                status_parts.append("现价接近平均成本")
            else:
                status_parts.append(f"现价低于平均成本{abs(cost_diff):.1f}%")

        return "，".join(status_parts)
