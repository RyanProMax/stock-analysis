"""
基本面因子库

动态映射财务数据字段到因子列表，支持多数据源
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from stockstats import StockDataFrame

from ..core import FactorDetail
from .base import FactorLibrary


def _format_market_cap(value: float, is_us: bool = False) -> str:
    """格式化市值（亿为单位）"""
    unit = "美元" if is_us else "人民币"
    if value >= 1e12:
        return f"{value / 1e12:.2f}万亿{unit}"
    return f"{value / 1e8:.2f}亿{unit}"


def _format_debt_ratio(value: float) -> str:
    """格式化负债率（倍数）"""
    return f"{value:.2f}倍"


# 各数据源字段 -> 内部key 的映射
FIELD_TO_KEY = {
    # 市盈率
    "trailingPE": "pe_ttm",
    "forwardPE": "pe_forward",
    "pe_ratio": "pe_ttm",
    # 市净率
    "priceToBook": "pb_ratio",
    "pb_ratio": "pb_ratio",
    # 盈利能力
    "returnOnEquity": "roe",
    "roe": "roe",
    "profitMargins": "profit_margin",
    "grossMargins": "gross_margin",
    "operatingMargins": "operating_margin",
    # 成长性
    "revenueGrowth": "revenue_growth",
    "revenue_growth": "revenue_growth",
    # 财务健康
    "debtToEquity": "debt_to_equity",
    "debt_ratio": "debt_ratio",
    "currentRatio": "current_ratio",
    "quickRatio": "quick_ratio",
    # 规模
    "marketCap": "market_cap",
}


# 内部key -> (中文名, 格式化函数)
# 注意: market_cap 的格式化需要 is_us 参数，在 get_factors 中特殊处理
KEY_FORMAT = {
    "pe_ttm": ("市盈率(TTM)", lambda v: f"{v:.2f}"),
    "pe_forward": ("远期市盈率", lambda v: f"{v:.2f}"),
    "pb_ratio": ("市净率", lambda v: f"{v:.2f}"),
    "roe": ("净资产收益率(ROE)", lambda v: f"{v * 100:.1f}%"),
    "profit_margin": ("利润率", lambda v: f"{v * 100:.1f}%"),
    "gross_margin": ("毛利率", lambda v: f"{v * 100:.1f}%"),
    "operating_margin": ("营业利润率", lambda v: f"{v * 100:.1f}%"),
    "revenue_growth": ("营收增长率", lambda v: f"{v * 100:.1f}%"),
    "debt_to_equity": ("负债权益比", _format_debt_ratio),
    "debt_ratio": ("资产负债率", lambda v: f"{v * 100:.1f}%"),
    "current_ratio": ("流动比率", lambda v: f"{v:.2f}"),
    "quick_ratio": ("速动比率", lambda v: f"{v:.2f}"),
}


class FundamentalFactorLibrary(FactorLibrary):
    """基本面因子库"""

    def get_factors(
        self,
        stock: StockDataFrame,
        raw_df: pd.DataFrame,
        financial_data: Optional[Dict[str, Any]] = None,
        data_source: str = "",
        **kwargs,
    ) -> List[FactorDetail]:
        """
        动态生成基本面因子列表

        Args:
            stock: StockDataFrame 对象
            raw_df: 原始行情数据 DataFrame
            financial_data: 财务数据字典（包含 raw_data）
            data_source: 数据源标识
            **kwargs: 其他参数

        Returns:
            List[FactorDetail]: 基本面因子列表
        """
        if not financial_data:
            return []

        factors = []
        raw_data = financial_data.get("raw_data", {})
        info_data = raw_data.get("info", {})
        collected = {}  # 内部key -> 值

        # 1. 收集 raw_data.info 字段
        for field, value in info_data.items():
            if field in FIELD_TO_KEY and value is not None:
                inner_key = FIELD_TO_KEY[field]
                collected[inner_key] = value

        # 2. 收集 financial_data 字段
        for field, value in financial_data.items():
            if field == "raw_data":
                continue
            if field in FIELD_TO_KEY and value is not None:
                inner_key = FIELD_TO_KEY[field]
                # raw_data 优先
                if inner_key not in collected:
                    collected[inner_key] = value

        # 3. 生成因子列表
        is_us = data_source.startswith("US_")
        for inner_key, value in collected.items():
            if inner_key == "market_cap":
                name = "市值"
                status = _format_market_cap(value, is_us)
            elif inner_key in KEY_FORMAT:
                name, formatter = KEY_FORMAT[inner_key]
                status = formatter(value)
            else:
                continue
            factors.append(
                FactorDetail(
                    key=inner_key,
                    name=name,
                    status=status,
                    bullish_signals=[],
                    bearish_signals=[],
                )
            )

        return factors
