"""
基本面因子库

包含所有基本面因子的计算逻辑：
- 营收增长率：反映公司成长性
- 资产负债率：反映财务健康度
- 市盈率（PE）：反映估值水平
- 市净率（PB）：反映资产价值
- ROE（净资产收益率）：反映盈利能力
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from stockstats import StockDataFrame

from ..model import FactorDetail
from .base import BaseFactor, FactorLibrary


class RevenueGrowthFactor(BaseFactor):
    """营收增长率因子"""

    def calculate(self, financial_data: Optional[Dict[str, Any]] = None, **kwargs) -> FactorDetail:
        """营收增长率因子分析：评估指标：反映公司成长性（>20% 优秀，<0% 衰退）"""
        bull, bear = [], []

        if financial_data is None:
            return FactorDetail(
                key="revenue_growth",
                name="营收增长率",
                category="基本面",
                status="-",
                bullish_signals=[],
                bearish_signals=[],
            )

        revenue_growth = financial_data.get("revenue_growth")
        if revenue_growth is None:
            return FactorDetail(
                key="revenue_growth",
                name="营收增长率",
                category="基本面",
                status="-",
                bullish_signals=[],
                bearish_signals=[],
            )

        if revenue_growth > 20:
            status = f"营收增长强劲 ({revenue_growth:.1f}%)"
            bull.append(
                self._create_signal(
                    "fundamental", f"营收增长强劲 ({revenue_growth:.1f}%)，成长性优秀"
                )
            )
        elif revenue_growth > 10:
            status = f"营收稳定增长 ({revenue_growth:.1f}%)"
            bull.append(self._create_signal("fundamental", f"营收稳定增长 ({revenue_growth:.1f}%)"))
        elif revenue_growth > 0:
            status = f"营收增长 ({revenue_growth:.1f}%)"
        elif revenue_growth > -10:
            status = f"营收增长放缓 ({revenue_growth:.1f}%)"
            bear.append(self._create_signal("fundamental", f"营收增长放缓 ({revenue_growth:.1f}%)"))
        else:
            status = f"营收负增长 ({revenue_growth:.1f}%)"
            bear.append(
                self._create_signal("fundamental", f"营收负增长 ({revenue_growth:.1f}%)，经营承压")
            )

        return FactorDetail(
            key="revenue_growth",
            name="营收增长率",
            category="基本面",
            status=status,
            bullish_signals=bull,
            bearish_signals=bear,
        )


class DebtRatioFactor(BaseFactor):
    """资产负债率因子"""

    def calculate(self, financial_data: Optional[Dict[str, Any]] = None, **kwargs) -> FactorDetail:
        """资产负债率因子分析：评估指标：反映财务健康度（<50% 健康，>70% 风险高）"""
        bull, bear = [], []

        if financial_data is None:
            return FactorDetail(
                key="debt_ratio",
                name="资产负债率",
                category="基本面",
                status="-",
                bullish_signals=[],
                bearish_signals=[],
            )

        debt_ratio = financial_data.get("debt_ratio")
        if debt_ratio is None:
            return FactorDetail(
                key="debt_ratio",
                name="资产负债率",
                category="基本面",
                status="-",
                bullish_signals=[],
                bearish_signals=[],
            )

        if debt_ratio < 30:
            status = f"负债率低 ({debt_ratio:.1f}%)"
            bull.append(
                self._create_signal("fundamental", f"负债率低 ({debt_ratio:.1f}%)，财务结构健康")
            )
        elif debt_ratio < 50:
            status = f"负债率适中 ({debt_ratio:.1f}%)"
            bull.append(self._create_signal("fundamental", f"负债率适中 ({debt_ratio:.1f}%)"))
        elif debt_ratio < 70:
            status = f"负债率偏高 ({debt_ratio:.1f}%)"
        else:
            status = f"负债率过高 ({debt_ratio:.1f}%)"
            bear.append(
                self._create_signal(
                    "fundamental", f"负债率偏高 ({debt_ratio:.1f}%)，财务风险需关注"
                )
            )

        return FactorDetail(
            key="debt_ratio",
            name="资产负债率",
            category="基本面",
            status=status,
            bullish_signals=bull,
            bearish_signals=bear,
        )


class PERatioFactor(BaseFactor):
    """市盈率（PE）因子"""

    def calculate(self, financial_data: Optional[Dict[str, Any]] = None, **kwargs) -> FactorDetail:
        """市盈率（PE）因子分析：评估指标：反映估值水平（<15 低估，>30 高估）"""
        bull, bear = [], []

        if financial_data is None:
            return FactorDetail(
                key="pe_ratio",
                name="市盈率",
                category="基本面",
                status="-",
                bullish_signals=[],
                bearish_signals=[],
            )

        pe_ratio = financial_data.get("pe_ratio")
        if pe_ratio is None or pe_ratio <= 0:
            return FactorDetail(
                key="pe_ratio",
                name="市盈率",
                category="基本面",
                status="-",
                bullish_signals=[],
                bearish_signals=[],
            )

        if pe_ratio < 10:
            status = f"PE 估值偏低 ({pe_ratio:.1f})"
            bull.append(
                self._create_signal("fundamental", f"PE={pe_ratio:.1f}，估值偏低，合理范围是 10-20")
            )
        elif pe_ratio < 20:
            status = f"PE 估值合理 ({pe_ratio:.1f})"
            bull.append(
                self._create_signal("fundamental", f"PE={pe_ratio:.1f}，估值合理，合理范围是 10-20")
            )
        elif pe_ratio < 30:
            status = f"PE 估值偏高 ({pe_ratio:.1f})"
        elif pe_ratio < 50:
            status = f"PE 估值过高 ({pe_ratio:.1f})"
            bear.append(
                self._create_signal("fundamental", f"PE={pe_ratio:.1f}，估值偏高，合理范围是 10-20")
            )
        else:
            status = f"PE 估值极高 ({pe_ratio:.1f})"
            bear.append(
                self._create_signal("fundamental", f"PE={pe_ratio:.1f}，估值过高，合理范围是 10-20")
            )

        return FactorDetail(
            key="pe_ratio",
            name="市盈率",
            category="基本面",
            status=status,
            bullish_signals=bull,
            bearish_signals=bear,
        )


class PBRatioFactor(BaseFactor):
    """市净率（PB）因子"""

    def calculate(self, financial_data: Optional[Dict[str, Any]] = None, **kwargs) -> FactorDetail:
        """市净率（PB）因子分析：评估指标：反映资产价值（<1 低估，>3 高估）"""
        bull, bear = [], []

        if financial_data is None:
            return FactorDetail(
                key="pb_ratio",
                name="市净率",
                category="基本面",
                status="-",
                bullish_signals=[],
                bearish_signals=[],
            )

        pb_ratio = financial_data.get("pb_ratio")
        if pb_ratio is None or pb_ratio <= 0:
            return FactorDetail(
                key="pb_ratio",
                name="市净率",
                category="基本面",
                status="-",
                bullish_signals=[],
                bearish_signals=[],
            )

        if pb_ratio < 1:
            status = f"PB 估值偏低 ({pb_ratio:.2f})"
            bull.append(
                self._create_signal("fundamental", f"PB={pb_ratio:.2f}，估值偏低，合理范围是 1-2")
            )
        elif pb_ratio < 2:
            status = f"PB 估值合理 ({pb_ratio:.2f})"
            bull.append(
                self._create_signal("fundamental", f"PB={pb_ratio:.2f}，估值合理，合理范围是 1-2")
            )
        elif pb_ratio < 3:
            status = f"PB 估值偏高 ({pb_ratio:.2f})"
        else:
            status = f"PB 估值过高 ({pb_ratio:.2f})"
            bear.append(
                self._create_signal("fundamental", f"PB={pb_ratio:.2f}，估值偏高，合理范围是 1-2")
            )

        return FactorDetail(
            key="pb_ratio",
            name="市净率",
            category="基本面",
            status=status,
            bullish_signals=bull,
            bearish_signals=bear,
        )


class ROEFactor(BaseFactor):
    """ROE（净资产收益率）因子"""

    def calculate(self, financial_data: Optional[Dict[str, Any]] = None, **kwargs) -> FactorDetail:
        """ROE（净资产收益率）因子分析：评估指标：反映盈利能力（>15% 优秀，<5% 较差）"""
        bull, bear = [], []

        if financial_data is None:
            return FactorDetail(
                key="roe",
                name="ROE",
                category="基本面",
                status="-",
                bullish_signals=[],
                bearish_signals=[],
            )

        roe = financial_data.get("roe")
        if roe is None:
            return FactorDetail(
                key="roe",
                name="ROE",
                category="基本面",
                status="-",
                bullish_signals=[],
                bearish_signals=[],
            )

        if roe > 20:
            status = f"ROE 优秀 ({roe:.1f}%)"
            bull.append(self._create_signal("fundamental", f"ROE优秀 ({roe:.1f}%)，盈利能力强劲"))
        elif roe > 15:
            status = f"ROE 良好 ({roe:.1f}%)"
            bull.append(self._create_signal("fundamental", f"ROE良好 ({roe:.1f}%)"))
        elif roe > 10:
            status = f"ROE 正常 ({roe:.1f}%)"
        elif roe > 5:
            status = f"ROE 偏低 ({roe:.1f}%)"
        else:
            status = f"ROE 较差 ({roe:.1f}%)"
            bear.append(self._create_signal("fundamental", f"ROE偏低 ({roe:.1f}%)，盈利能力较弱"))

        return FactorDetail(
            key="roe",
            name="ROE",
            category="基本面",
            status=status,
            bullish_signals=bull,
            bearish_signals=bear,
        )


class FundamentalFactorLibrary(FactorLibrary):
    """基本面因子库"""

    def get_factors(
        self,
        stock: StockDataFrame,
        raw_df: pd.DataFrame,
        financial_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> List[FactorDetail]:
        """
        获取所有基本面因子

        Args:
            stock: StockDataFrame 对象
            raw_df: 原始行情数据 DataFrame
            financial_data: 财务数据字典
            **kwargs: 其他参数

        Returns:
            List[FactorDetail]: 基本面因子列表
        """
        factors = []

        factors.append(RevenueGrowthFactor(stock, raw_df).calculate(financial_data=financial_data))
        factors.append(DebtRatioFactor(stock, raw_df).calculate(financial_data=financial_data))
        factors.append(PERatioFactor(stock, raw_df).calculate(financial_data=financial_data))
        factors.append(PBRatioFactor(stock, raw_df).calculate(financial_data=financial_data))
        factors.append(ROEFactor(stock, raw_df).calculate(financial_data=financial_data))

        return factors
