# -*- coding: utf-8 -*-
"""
DCF 估值模型数据类型定义

包含 DCF 分析相关的所有数据类
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class WACCComponents:
    """WACC (加权平均资本成本) 组成部分"""

    risk_free_rate: float = 0.042  # 无风险利率 (10年期国债)
    equity_risk_premium: float = 0.055  # 股权风险溢价
    beta: float = 1.0  # Beta 系数
    cost_of_equity: float = 0.0  # 股权成本
    cost_of_debt: float = 0.0  # 债务成本 (税前)
    cost_of_debt_after_tax: float = 0.0  # 债务成本 (税后)
    tax_rate: float = 0.25  # 税率

    # 资本结构
    market_cap: float = 0.0  # 市值
    net_debt: float = 0.0  # 净债务
    enterprise_value: float = 0.0  # 企业价值
    equity_weight: float = 0.0  # 股权权重
    debt_weight: float = 0.0  # 债务权重

    # 最终 WACC
    wacc: float = 0.0


@dataclass
class FCFProjection:
    """自由现金流预测"""

    year: int  # 预测年份 (1-5)
    revenue: float  # 收入预测
    revenue_growth: float  # 收入增长率
    ebitda: float  # EBITDA
    ebitda_margin: float  # EBITDA 利润率
    ebit: float  # EBIT
    tax_rate: float  # 税率
    nopat: float  # 税后净营业利润
    da: float  # 折旧摊销
    capex: float  # 资本支出
    delta_nwc: float  # 营运资本变化
    fcf: float  # 自由现金流
    discount_factor: float  # 折现因子
    pv_fcf: float  # 自由现金流现值


@dataclass
class TerminalValue:
    """终值计算"""

    terminal_fcf: float = 0.0  # 终期 FCF
    terminal_growth_rate: float = 0.025  # 永续增长率
    exit_multiple: float = 0.0  # 退出倍数 (可选)
    terminal_value: float = 0.0  # 终值
    pv_terminal: float = 0.0  # 终值现值
    terminal_value_pct: float = 0.0  # 终值占比


@dataclass
class SensitivityMatrix:
    """敏感性分析矩阵 - 3个25格矩阵，共75格"""

    # 矩阵1: WACC vs Terminal Growth Rate (5×5 = 25格)
    wacc_values: List[float] = field(default_factory=list)
    terminal_growth_values: List[float] = field(default_factory=list)
    price_matrix_wacc_growth: List[List[float]] = field(default_factory=list)

    # 矩阵2: Revenue Growth vs EBITDA Margin (5×5 = 25格)
    revenue_growth_values: List[float] = field(default_factory=list)
    ebitda_margin_values: List[float] = field(default_factory=list)
    price_matrix_growth_margin: List[List[float]] = field(default_factory=list)

    # 矩阵3: Exit Multiple vs WACC (5×5 = 25格)
    exit_multiple_values: List[float] = field(default_factory=list)
    wacc_values_2: List[float] = field(default_factory=list)
    price_matrix_multiple_wacc: List[List[float]] = field(default_factory=list)


@dataclass
class ValuationRange:
    """估值区间"""

    bear_case: float = 0.0  # 熊市估值
    base_case: float = 0.0  # 基准估值
    bull_case: float = 0.0  # 牛市估值

    # 倍数法估值区间
    low: float = 0.0
    mid: float = 0.0
    high: float = 0.0


@dataclass
class DCFResult:
    """DCF 估值结果"""

    # 基本信息
    symbol: str
    company_name: str = ""
    current_price: float = 0.0
    currency: str = "USD"

    # 估值结果
    enterprise_value: float = 0.0  # 企业价值 (百万)
    equity_value: float = 0.0  # 股权价值 (百万)
    implied_price: float = 0.0  # 隐含股价
    upside: float = 0.0  # 上涨空间 (%)

    # WACC 组成
    wacc_components: WACCComponents = field(default_factory=WACCComponents)

    # FCF 预测
    fcf_projections: List[FCFProjection] = field(default_factory=list)

    # 终值
    terminal_value: TerminalValue = field(default_factory=TerminalValue)

    # 估值分解
    pv_fcf_sum: float = 0.0  # FCF 现值总和 (百万)
    pv_terminal: float = 0.0  # 终值现值 (百万)

    # 敏感性分析
    sensitivity: SensitivityMatrix = field(default_factory=SensitivityMatrix)

    # 估值区间
    valuation_range: ValuationRange = field(default_factory=ValuationRange)

    # 评级
    recommendation: str = "HOLD"  # BUY / HOLD / SELL
    confidence: str = "MEDIUM"  # HIGH / MEDIUM / LOW

    # 分析假设
    assumptions: Dict[str, Any] = field(default_factory=dict)

    # 错误信息
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "symbol": self.symbol,
            "company_name": self.company_name,
            "current_price": self.current_price,
            "currency": self.currency,
            "enterprise_value": round(self.enterprise_value, 2),
            "equity_value": round(self.equity_value, 2),
            "implied_price": round(self.implied_price, 2),
            "upside": round(self.upside, 2),
            "wacc": round(self.wacc_components.wacc * 100, 2),
            "wacc_components": {
                "risk_free_rate": round(self.wacc_components.risk_free_rate * 100, 2),
                "equity_risk_premium": round(self.wacc_components.equity_risk_premium * 100, 2),
                "beta": round(self.wacc_components.beta, 2),
                "cost_of_equity": round(self.wacc_components.cost_of_equity * 100, 2),
                "cost_of_debt": round(self.wacc_components.cost_of_debt * 100, 2),
                "tax_rate": round(self.wacc_components.tax_rate * 100, 2),
                "equity_weight": round(self.wacc_components.equity_weight * 100, 2),
                "debt_weight": round(self.wacc_components.debt_weight * 100, 2),
            },
            "fcf_projections": [
                {
                    "year": p.year,
                    "revenue": round(p.revenue / 1e6, 2),
                    "revenue_growth": round(p.revenue_growth * 100, 2),
                    "ebitda_margin": round(p.ebitda_margin * 100, 2),
                    "fcf": round(p.fcf / 1e6, 2),
                    "pv_fcf": round(p.pv_fcf / 1e6, 2),
                }
                for p in self.fcf_projections
            ],
            "terminal_value": {
                "terminal_growth_rate": round(self.terminal_value.terminal_growth_rate * 100, 2),
                "terminal_value_pct": round(self.terminal_value.terminal_value_pct * 100, 2),
            },
            "valuation_summary": {
                "pv_fcf_sum": round(self.pv_fcf_sum, 2),
                "pv_terminal": round(self.pv_terminal, 2),
                "enterprise_value": round(self.enterprise_value, 2),
            },
            "sensitivity": {
                # 矩阵1: WACC vs Terminal Growth Rate
                "wacc_vs_growth": {
                    "wacc_values": [round(v * 100, 1) for v in self.sensitivity.wacc_values],
                    "growth_values": [
                        round(v * 100, 1) for v in self.sensitivity.terminal_growth_values
                    ],
                    "price_matrix": [
                        [round(p, 2) for p in row]
                        for row in self.sensitivity.price_matrix_wacc_growth
                    ],
                },
                # 矩阵2: Revenue Growth vs EBITDA Margin
                "growth_vs_margin": {
                    "revenue_growth_values": [
                        round(v * 100, 1) for v in self.sensitivity.revenue_growth_values
                    ],
                    "ebitda_margin_values": [
                        round(v * 100, 1) for v in self.sensitivity.ebitda_margin_values
                    ],
                    "price_matrix": [
                        [round(p, 2) for p in row]
                        for row in self.sensitivity.price_matrix_growth_margin
                    ],
                },
                # 矩阵3: Exit Multiple vs WACC
                "multiple_vs_wacc": {
                    "exit_multiple_values": [
                        round(v, 1) for v in self.sensitivity.exit_multiple_values
                    ],
                    "wacc_values": [round(v * 100, 1) for v in self.sensitivity.wacc_values_2],
                    "price_matrix": [
                        [round(p, 2) for p in row]
                        for row in self.sensitivity.price_matrix_multiple_wacc
                    ],
                },
            },
            "valuation_range": {
                "bear": round(self.valuation_range.bear_case, 2),
                "base": round(self.valuation_range.base_case, 2),
                "bull": round(self.valuation_range.bull_case, 2),
            },
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "error": self.error,
        }
