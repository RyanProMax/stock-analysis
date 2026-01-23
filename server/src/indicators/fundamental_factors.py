"""
���本面因子库

包含所有基本面因子的计算逻辑：
- 营收增长率：反映公司成长性
- 资产负债率：反映财务健康度
- 市盈率（PE）：反映估值水平
- 市净率（PB）：反映资产价值
- ROE（净资产收益率）：反映盈利能力

注意：基本面因子仅返回客观数值，不生成主观评价信号。
评价分析由 LLM 在 /agent/analyze 接口中结合行业数据进行综合判断。
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from stockstats import StockDataFrame

from ..core import FactorDetail
from .base import BaseFactor, FactorLibrary


class RevenueGrowthFactor(BaseFactor):
    """营收增长率因子"""

    def calculate(
        self,
        financial_data: Optional[Dict[str, Any]] = None,
        data_source: str = "",
        **kwargs,
    ) -> FactorDetail:
        """营收增长率因子：返回客观数值"""
        if financial_data is None:
            return FactorDetail(
                key="revenue_growth",
                name="营收增长率",
                status="数据不可用",
                bullish_signals=[],
                bearish_signals=[],
                data_source=data_source,
            )

        revenue_growth = financial_data.get("revenue_growth")
        if revenue_growth is None:
            return FactorDetail(
                key="revenue_growth",
                name="营收增长率",
                status="数据不可用",
                bullish_signals=[],
                bearish_signals=[],
                data_source=data_source,
            )

        # 仅返回客观数值，不做主观判断
        return FactorDetail(
            key="revenue_growth",
            name="营收增长率",
            status=f"{revenue_growth:.1f}%",
            bullish_signals=[],
            bearish_signals=[],
            data_source=data_source,
        )


class DebtRatioFactor(BaseFactor):
    """资产负债率因子"""

    def calculate(
        self,
        financial_data: Optional[Dict[str, Any]] = None,
        data_source: str = "",
        **kwargs,
    ) -> FactorDetail:
        """资产负债率因子：返回客观数值"""
        if financial_data is None:
            return FactorDetail(
                key="debt_ratio",
                name="资产负债率",
                status="数据不可用",
                bullish_signals=[],
                bearish_signals=[],
                data_source=data_source,
            )

        debt_ratio = financial_data.get("debt_ratio")
        if debt_ratio is None:
            return FactorDetail(
                key="debt_ratio",
                name="资产负债率",
                status="数据不可用",
                bullish_signals=[],
                bearish_signals=[],
                data_source=data_source,
            )

        # 仅返回客观数值
        return FactorDetail(
            key="debt_ratio",
            name="资产负债率",
            status=f"{debt_ratio:.1f}%",
            bullish_signals=[],
            bearish_signals=[],
            data_source=data_source,
        )


class PERatioFactor(BaseFactor):
    """市盈率（PE）因子"""

    def calculate(
        self,
        financial_data: Optional[Dict[str, Any]] = None,
        data_source: str = "",
        **kwargs,
    ) -> FactorDetail:
        """市盈率（PE）因子：返回客观数值"""
        if financial_data is None:
            return FactorDetail(
                key="pe_ratio",
                name="市盈率(PE)",
                status="数据不可用",
                bullish_signals=[],
                bearish_signals=[],
                data_source=data_source,
            )

        pe_ratio = financial_data.get("pe_ratio")
        if pe_ratio is None or pe_ratio <= 0:
            return FactorDetail(
                key="pe_ratio",
                name="市盈率(PE)",
                status="数据不可用",
                bullish_signals=[],
                bearish_signals=[],
                data_source=data_source,
            )

        # 仅返回客观数值
        return FactorDetail(
            key="pe_ratio",
            name="市盈率(PE)",
            status=f"{pe_ratio:.1f}",
            bullish_signals=[],
            bearish_signals=[],
            data_source=data_source,
        )


class PBRatioFactor(BaseFactor):
    """市净率（PB）因子"""

    def calculate(
        self,
        financial_data: Optional[Dict[str, Any]] = None,
        data_source: str = "",
        **kwargs,
    ) -> FactorDetail:
        """市净率（PB）因子：返回客观数值"""
        if financial_data is None:
            return FactorDetail(
                key="pb_ratio",
                name="市净率(PB)",
                status="数据不可用",
                bullish_signals=[],
                bearish_signals=[],
                data_source=data_source,
            )

        pb_ratio = financial_data.get("pb_ratio")
        if pb_ratio is None or pb_ratio <= 0:
            return FactorDetail(
                key="pb_ratio",
                name="市净率(PB)",
                status="数据不可用",
                bullish_signals=[],
                bearish_signals=[],
                data_source=data_source,
            )

        # 仅返回客观数值
        return FactorDetail(
            key="pb_ratio",
            name="市净率(PB)",
            status=f"{pb_ratio:.2f}",
            bullish_signals=[],
            bearish_signals=[],
            data_source=data_source,
        )


class ROEFactor(BaseFactor):
    """ROE（净资产收益率）因子"""

    def calculate(
        self,
        financial_data: Optional[Dict[str, Any]] = None,
        data_source: str = "",
        **kwargs,
    ) -> FactorDetail:
        """ROE（净资产收益率）因子：返回客观数值"""
        if financial_data is None:
            return FactorDetail(
                key="roe",
                name="净资产收益率(ROE)",
                status="数据不可用",
                bullish_signals=[],
                bearish_signals=[],
                data_source=data_source,
            )

        roe = financial_data.get("roe")
        if roe is None:
            return FactorDetail(
                key="roe",
                name="净资产收益率(ROE)",
                status="数据不可用",
                bullish_signals=[],
                bearish_signals=[],
                data_source=data_source,
            )

        # 仅返回客观数值
        return FactorDetail(
            key="roe",
            name="净资产收益率(ROE)",
            status=f"{roe:.1f}%",
            bullish_signals=[],
            bearish_signals=[],
            data_source=data_source,
        )


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
        获取所有基本面因子（仅客观数值，不包含主观评价）

        Args:
            stock: StockDataFrame 对象
            raw_df: 原始行情数据 DataFrame
            financial_data: 财务数据字典
            data_source: 数据源标识
            raw_data: 原始数据
            **kwargs: 其他参数

        Returns:
            List[FactorDetail]: 基本面因子列表
        """
        factors = []

        factors.append(
            RevenueGrowthFactor(stock, raw_df).calculate(
                financial_data=financial_data, data_source=data_source
            )
        )
        factors.append(
            DebtRatioFactor(stock, raw_df).calculate(
                financial_data=financial_data, data_source=data_source
            )
        )
        factors.append(
            PERatioFactor(stock, raw_df).calculate(
                financial_data=financial_data, data_source=data_source
            )
        )
        factors.append(
            PBRatioFactor(stock, raw_df).calculate(
                financial_data=financial_data, data_source=data_source
            )
        )
        factors.append(
            ROEFactor(stock, raw_df).calculate(
                financial_data=financial_data, data_source=data_source
            )
        )

        return factors
