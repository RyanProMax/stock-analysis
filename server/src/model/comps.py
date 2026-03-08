# -*- coding: utf-8 -*-
"""
可比公司分析 (Comps) 数据类型定义

包含 Comps 分析相关的所有数据类
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class CompCompany:
    """可比公司基本信息"""

    symbol: str
    company_name: str
    sector: str
    industry: str

    # 市值和估值
    market_cap: float = 0.0  # 市值 (百万)
    enterprise_value: float = 0.0  # 企业价值 (百万)

    # 股价
    current_price: float = 0.0
    currency: str = "USD"

    # 运营指标 (TTM)
    revenue: float = 0.0  # 收入 (百万)
    revenue_growth: float = 0.0  # 收入增长率
    gross_margin: float = 0.0  # 毛利率
    ebitda: float = 0.0  # EBITDA (百万)
    ebitda_margin: float = 0.0  # EBITDA 利润率
    ebit: float = 0.0  # EBIT (百万)
    net_income: float = 0.0  # 净利润 (百万)
    fcf: float = 0.0  # 自由现金流 (百万)
    fcf_margin: float = 0.0  # FCF 利润率

    # SaaS 特定指标
    rule_of_40: float = 0.0  # Rule of 40 score
    arr: float = 0.0  # ARR (百万)
    cac: float = 0.0  # 客户获取成本
    ltv: float = 0.0  # 客户生命周期价值
    ltv_cac_ratio: float = 0.0  # LTV/CAC 比率

    # 估值倍数 (TTM)
    pe_ratio: float = 0.0  # P/E
    ps_ratio: float = 0.0  # P/S
    pb_ratio: float = 0.0  # P/B
    ev_ebitda: float = 0.0  # EV/EBITDA
    ev_revenue: float = 0.0  # EV/Revenue
    ev_fcf: float = 0.0  # EV/FCF


@dataclass
class OperatingMetrics:
    """运营指标统计"""

    # 收入
    revenue_avg: float = 0.0
    revenue_median: float = 0.0

    # 增长率
    growth_avg: float = 0.0
    growth_median: float = 0.0

    # 利润率
    gross_margin_avg: float = 0.0
    gross_margin_median: float = 0.0
    ebitda_margin_avg: float = 0.0
    ebitda_margin_median: float = 0.0
    fcf_margin_avg: float = 0.0
    fcf_margin_median: float = 0.0


@dataclass
class ValuationMultiples:
    """估值倍数统计"""

    # P/E
    pe_avg: float = 0.0
    pe_median: float = 0.0

    # P/S
    ps_avg: float = 0.0
    ps_median: float = 0.0

    # P/B
    pb_avg: float = 0.0
    pb_median: float = 0.0

    # EV/EBITDA
    ev_ebitda_avg: float = 0.0
    ev_ebitda_median: float = 0.0

    # EV/Revenue
    ev_revenue_avg: float = 0.0
    ev_revenue_median: float = 0.0

    # EV/FCF
    ev_fcf_avg: float = 0.0
    ev_fcf_median: float = 0.0


@dataclass
class PercentileAnalysis:
    """分位数分析"""

    # 估值倍数分位数 (25th, 50th, 75th)
    pe_25th: float = 0.0
    pe_50th: float = 0.0
    pe_75th: float = 0.0

    ps_25th: float = 0.0
    ps_50th: float = 0.0
    ps_75th: float = 0.0

    pb_25th: float = 0.0
    pb_50th: float = 0.0
    pb_75th: float = 0.0

    ev_ebitda_25th: float = 0.0
    ev_ebitda_50th: float = 0.0
    ev_ebitda_75th: float = 0.0

    # 运营指标分位数
    revenue_growth_25th: float = 0.0
    revenue_growth_50th: float = 0.0
    revenue_growth_75th: float = 0.0

    gross_margin_25th: float = 0.0
    gross_margin_50th: float = 0.0
    gross_margin_75th: float = 0.0

    ebitda_margin_25th: float = 0.0
    ebitda_margin_50th: float = 0.0
    ebitda_margin_75th: float = 0.0


@dataclass
class CompsResult:
    """可比公司分析结果"""

    # 目标公司
    target_symbol: str
    target_name: str = ""
    sector: str = ""
    industry: str = ""

    # 可比公司列表
    comps: List[CompCompany] = field(default_factory=list)

    # 统计指标
    operating_metrics: OperatingMetrics = field(default_factory=OperatingMetrics)
    valuation_multiples: ValuationMultiples = field(default_factory=ValuationMultiples)
    percentiles: PercentileAnalysis = field(default_factory=PercentileAnalysis)

    # 目标公司估值 (基于中位数)
    implied_pe_low: float = 0.0  # 基于 25th 分位数
    implied_pe_mid: float = 0.0  # 基于 50th 分位数
    implied_pe_high: float = 0.0  # 基于 75th 分位数

    implied_ps_low: float = 0.0
    implied_ps_mid: float = 0.0
    implied_ps_high: float = 0.0

    implied_ev_ebitda_low: float = 0.0
    implied_ev_ebitda_mid: float = 0.0
    implied_ev_ebitda_high: float = 0.0

    # 建议
    recommendation: str = "HOLD"  # UNDERVALUED / FAIR / OVERVALUED
    confidence: str = "MEDIUM"  # HIGH / MEDIUM / LOW

    # 错误信息
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "target_symbol": self.target_symbol,
            "target_name": self.target_name,
            "sector": self.sector,
            "industry": self.industry,
            "comps_count": len(self.comps),
            "comps": [
                {
                    "symbol": c.symbol,
                    "company_name": c.company_name,
                    "sector": c.sector,
                    "industry": c.industry,
                    "market_cap": round(c.market_cap, 2),
                    "enterprise_value": round(c.enterprise_value, 2),
                    "current_price": round(c.current_price, 2),
                    "revenue": round(c.revenue, 2),
                    "revenue_growth": round(c.revenue_growth * 100, 2),
                    "gross_margin": round(c.gross_margin * 100, 2),
                    "ebitda_margin": round(c.ebitda_margin * 100, 2),
                    "fcf_margin": round(c.fcf_margin * 100, 2),
                    "pe_ratio": round(c.pe_ratio, 2) if c.pe_ratio > 0 else None,
                    "ps_ratio": round(c.ps_ratio, 2) if c.ps_ratio > 0 else None,
                    "pb_ratio": round(c.pb_ratio, 2) if c.pb_ratio > 0 else None,
                    "ev_ebitda": round(c.ev_ebitda, 2) if c.ev_ebitda > 0 else None,
                    "ev_revenue": round(c.ev_revenue, 2) if c.ev_revenue > 0 else None,
                    "ev_fcf": round(c.ev_fcf, 2) if c.ev_fcf > 0 else None,
                    "rule_of_40": round(c.rule_of_40, 2) if c.rule_of_40 != 0 else None,
                }
                for c in self.comps
            ],
            "operating_metrics": {
                "revenue_avg": round(self.operating_metrics.revenue_avg, 2),
                "revenue_median": round(self.operating_metrics.revenue_median, 2),
                "growth_avg": round(self.operating_metrics.growth_avg * 100, 2),
                "growth_median": round(self.operating_metrics.growth_median * 100, 2),
                "gross_margin_avg": round(self.operating_metrics.gross_margin_avg * 100, 2),
                "gross_margin_median": round(self.operating_metrics.gross_margin_median * 100, 2),
                "ebitda_margin_avg": round(self.operating_metrics.ebitda_margin_avg * 100, 2),
                "ebitda_margin_median": round(self.operating_metrics.ebitda_margin_median * 100, 2),
                "fcf_margin_avg": round(self.operating_metrics.fcf_margin_avg * 100, 2),
                "fcf_margin_median": round(self.operating_metrics.fcf_margin_median * 100, 2),
            },
            "valuation_multiples": {
                "pe_avg": round(self.valuation_multiples.pe_avg, 2),
                "pe_median": round(self.valuation_multiples.pe_median, 2),
                "ps_avg": round(self.valuation_multiples.ps_avg, 2),
                "ps_median": round(self.valuation_multiples.ps_median, 2),
                "pb_avg": round(self.valuation_multiples.pb_avg, 2),
                "pb_median": round(self.valuation_multiples.pb_median, 2),
                "ev_ebitda_avg": round(self.valuation_multiples.ev_ebitda_avg, 2),
                "ev_ebitda_median": round(self.valuation_multiples.ev_ebitda_median, 2),
                "ev_revenue_avg": round(self.valuation_multiples.ev_revenue_avg, 2),
                "ev_revenue_median": round(self.valuation_multiples.ev_revenue_median, 2),
                "ev_fcf_avg": round(self.valuation_multiples.ev_fcf_avg, 2),
                "ev_fcf_median": round(self.valuation_multiples.ev_fcf_median, 2),
            },
            "percentiles": {
                "pe": {
                    "25th": round(self.percentiles.pe_25th, 2),
                    "50th": round(self.percentiles.pe_50th, 2),
                    "75th": round(self.percentiles.pe_75th, 2),
                },
                "ps": {
                    "25th": round(self.percentiles.ps_25th, 2),
                    "50th": round(self.percentiles.ps_50th, 2),
                    "75th": round(self.percentiles.ps_75th, 2),
                },
                "pb": {
                    "25th": round(self.percentiles.pb_25th, 2),
                    "50th": round(self.percentiles.pb_50th, 2),
                    "75th": round(self.percentiles.pb_75th, 2),
                },
                "ev_ebitda": {
                    "25th": round(self.percentiles.ev_ebitda_25th, 2),
                    "50th": round(self.percentiles.ev_ebitda_50th, 2),
                    "75th": round(self.percentiles.ev_ebitda_75th, 2),
                },
                "revenue_growth": {
                    "25th": round(self.percentiles.revenue_growth_25th * 100, 2),
                    "50th": round(self.percentiles.revenue_growth_50th * 100, 2),
                    "75th": round(self.percentiles.revenue_growth_75th * 100, 2),
                },
                "gross_margin": {
                    "25th": round(self.percentiles.gross_margin_25th * 100, 2),
                    "50th": round(self.percentiles.gross_margin_50th * 100, 2),
                    "75th": round(self.percentiles.gross_margin_75th * 100, 2),
                },
                "ebitda_margin": {
                    "25th": round(self.percentiles.ebitda_margin_25th * 100, 2),
                    "50th": round(self.percentiles.ebitda_margin_50th * 100, 2),
                    "75th": round(self.percentiles.ebitda_margin_75th * 100, 2),
                },
            },
            "implied_valuation": {
                "pe": {
                    "low": round(self.implied_pe_low, 2),
                    "mid": round(self.implied_pe_mid, 2),
                    "high": round(self.implied_pe_high, 2),
                },
                "ps": {
                    "low": round(self.implied_ps_low, 2),
                    "mid": round(self.implied_ps_mid, 2),
                    "high": round(self.implied_ps_high, 2),
                },
                "ev_ebitda": {
                    "low": round(self.implied_ev_ebitda_low, 2),
                    "mid": round(self.implied_ev_ebitda_mid, 2),
                    "high": round(self.implied_ev_ebitda_high, 2),
                },
            },
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "error": self.error,
        }
