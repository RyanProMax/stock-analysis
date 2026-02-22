"""
基本面因子库

动态映射财务数据字段到因子列表，支持多数据源
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from stockstats import StockDataFrame

from ..core import FactorDetail
from .base import FactorLibrary


def _format_market_cap(value: float) -> str:
    """格式化市值"""
    if value >= 1e12:
        return f"{value / 1e12:.2f}万亿"
    return f"{value / 1e8:.2f}亿"


def _format_percent(value: float) -> str:
    """格式化百分比"""
    return f"{value * 100:.2f}%"


def _format_number(value: float) -> str:
    """格式化数值"""
    return f"{value:.2f}"


# yfinance info 字段映射: 字段名 -> (中文名, 格式化函数)
YFINANCE_FIELD_MAP = {
    # 估值
    "trailingPE": ("市盈率(TTM)", _format_number),
    "forwardPE": ("远期市盈率", _format_number),
    "pegRatio": ("PEG比率", _format_number),
    "priceToBook": ("市净率", _format_number),
    "priceToSalesTrailing12Months": ("市销率", _format_number),
    "enterpriseToEbitda": ("EV/EBITDA", _format_number),
    "enterpriseToRevenue": ("EV/营收", _format_number),
    # 盈利能力
    "profitMargins": ("利润率", _format_percent),
    "grossMargins": ("毛利率", _format_percent),
    "operatingMargins": ("营业利润率", _format_percent),
    "ebitdaMargins": ("EBITDA利润率", _format_percent),
    "returnOnAssets": ("总资产回报率(ROA)", _format_percent),
    "returnOnEquity": ("净资产收益率(ROE)", _format_percent),
    # 成长性
    "revenueGrowth": ("营收增长率", _format_percent),
    "earningsGrowth": ("盈利增长率", _format_percent),
    "earningsQuarterlyGrowth": ("季度盈利增长", _format_percent),
    # 财务健康
    "currentRatio": ("流动比率", _format_number),
    "quickRatio": ("速动比率", _format_number),
    "debtToEquity": ("负债权益比", _format_number),
    # 规模
    "marketCap": ("市值", _format_market_cap),
    "enterpriseValue": ("企业价值", _format_market_cap),
    "totalCash": ("现金", _format_market_cap),
    "totalDebt": ("总债务", _format_market_cap),
    "totalRevenue": ("总收入", _format_market_cap),
    "bookValue": ("每股账面价值", _format_number),
    # 现金流
    "operatingCashflow": ("经营现金流", _format_market_cap),
    "freeCashflow": ("自由现金流", _format_market_cap),
    "ebitda": ("EBITDA", _format_market_cap),
    "netIncomeToCommon": ("净利润", _format_market_cap),
    "grossProfits": ("毛利润", _format_market_cap),
    # 交易数据
    "beta": ("Beta系数", _format_number),
    "trailingEps": ("每股收益(TTM)", _format_number),
    "forwardEps": ("远期每股收益", _format_number),
    "revenuePerShare": ("每股营收", _format_number),
    "dividendYield": ("股息率", _format_percent),
    "payoutRatio": ("派息比率", _format_percent),
    # 分析师预期
    "targetMeanPrice": ("分析师目标价均值", _format_number),
    "targetHighPrice": ("分析师目标价上限", _format_number),
    "targetLowPrice": ("分析师目标价下限", _format_number),
    "numberOfAnalystOpinions": ("覆盖分析师数", lambda v: f"{int(v)}"),
    # 股本结构
    "sharesOutstanding": ("流通股本", lambda v: f"{v / 1e8:.2f}亿股"),
    "floatShares": ("自由流通股本", lambda v: f"{v / 1e8:.2f}亿股"),
    "heldPercentInsiders": ("内部人持股比例", _format_percent),
    "heldPercentInstitutions": ("机构持股比例", _format_percent),
    "sharesPercentSharesOut": ("做空比例", _format_percent),
}


# A股数据源字段映射
CN_FIELD_MAP = {
    "pe_ratio": ("市盈率(PE)", _format_number),
    "pb_ratio": ("市净率(PB)", _format_number),
    "roe": ("净资产收益率(ROE)", lambda v: f"{v:.1f}%"),
    "revenue_growth": ("营收增长率", lambda v: f"{v:.1f}%"),
    "debt_ratio": ("资产负债率", lambda v: f"{v:.1f}%"),
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

        # 1. 处理 raw_data.info（美股 yfinance）
        for field, (name, formatter) in YFINANCE_FIELD_MAP.items():
            value = info_data.get(field)
            if value is not None and value != 0:
                factors.append(
                    FactorDetail(
                        key=field,
                        name=name,
                        status=formatter(value),
                        bullish_signals=[],
                        bearish_signals=[],
                    )
                )

        # 2. 处理 financial_data（A股数据源）
        for field, (name, formatter) in CN_FIELD_MAP.items():
            value = financial_data.get(field)
            if value is not None and value != 0 and field not in info_data:
                factors.append(
                    FactorDetail(
                        key=field,
                        name=name,
                        status=formatter(value),
                        bullish_signals=[],
                        bearish_signals=[],
                    )
                )

        return factors
