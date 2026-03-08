# -*- coding: utf-8 -*-
"""
可比公司分析 (Comps Analysis)

基于行业、市值、收入规模筛选可比公司，计算运营指标和估值倍数
"""

import yfinance as yf
import numpy as np
from typing import List, Dict, Optional

from ..model import (
    CompsResult,
    CompCompany,
    OperatingMetrics,
    ValuationMultiples,
    PercentileAnalysis,
)


# 行业映射 - 用于查找可比公司
INDUSTRY_COMPS: Dict[str, List[str]] = {
    "Technology": [
        "MSFT",
        "GOOGL",
        "META",
        "AMZN",
        "ORCL",
        "CRM",
        "ADBE",
        "CSCO",
        "INTC",
        "IBM",
    ],
    "Software": [
        "MSFT",
        "ADBE",
        "CRM",
        "ORCL",
        "SAP",
        "INTU",
        "WDAY",
        "SNOW",
        "TEAM",
        "DDOG",
    ],
    "Semiconductors": [
        "NVDA",
        "AMD",
        "INTC",
        "TSM",
        "AVGO",
        "QCOM",
        "TXN",
        "AMAT",
        "LRCX",
        "MU",
    ],
    "Consumer Electronics": ["AAPL", "MSFT", "GOOGL", "AMZN", "SAMSUNG", "SONY", "LG"],
    "E-commerce": [
        "AMZN",
        "SHOP",
        "WMT",
        "TGT",
        "COST",
        "HD",
        "LOW",
        "EBAY",
        "ETSY",
        "W",
    ],
    "Cloud Computing": [
        "AMZN",
        "MSFT",
        "GOOGL",
        "ORCL",
        "IBM",
        "Salesforce",
        "SAP",
        "WORK",
        "ZM",
        "DOCU",
    ],
    "Financial Services": [
        "JPM",
        "BAC",
        "WFC",
        "C",
        "GS",
        "MS",
        "AXP",
        "V",
        "MA",
        "PYPL",
    ],
    "Healthcare": [
        "JNJ",
        "UNH",
        "PFE",
        "ABBV",
        "TMO",
        "ABT",
        "MRK",
        "LLY",
        "AMGN",
        "GILD",
    ],
    "Biotechnology": [
        "MRNA",
        "REGN",
        "VRTX",
        "GILD",
        "BIIB",
        "AMGN",
        "SGEN",
        "EXAS",
        "ILMN",
        "TECH",
    ],
    "Media": ["GOOGL", "META", "NFLX", "DIS", "CMCSA", "T", "VZ", "PARA", "WBD", "EA"],
    "Entertainment": [
        "DIS",
        "NFLX",
        "CMCSA",
        "T",
        "PARA",
        "WBD",
        "SONY",
        "NWSA",
        "FOX",
        "AMCX",
    ],
    "Telecom": [
        "T",
        "VZ",
        "TMUS",
        "CMCSA",
        "CHTR",
        "DIS",
        "NFLX",
        "GOOGL",
        "AMZN",
        "META",
    ],
    "Retail": ["WMT", "AMZN", "TGT", "COST", "HD", "LOW", "CVS", "DG", "DLTR", "BBY"],
    "Automotive": [
        "TSLA",
        "GM",
        "F",
        "TM",
        "HMC",
        "STLA",
        "RIVN",
        "LCID",
        "NIO",
        "XPEV",
    ],
    "Energy": ["XOM", "CVX", "COP", "EOG", "SLB", "MPC", "VLO", "PSX", "OXY", "HAL"],
    "Aerospace": ["BA", "LMT", "RTX", "NOC", "GD", "LHX", "TXT", "HII", "ASA", "AIR"],
    "Industrial": ["CAT", "DE", "BA", "GE", "MMM", "HON", "UPS", "FDX", "RSG", "EMR"],
    "Real Estate": [
        "PLD",
        "AMT",
        "CCI",
        "EQIX",
        "PSA",
        "SPG",
        "O",
        "WELL",
        "AVB",
        "EQR",
    ],
    "Banking": ["JPM", "BAC", "WFC", "C", "GS", "MS", "BK", "USB", "PNC", "TFC"],
    "Insurance": [
        "BRK.B",
        "PRU",
        "MET",
        "ALL",
        "TRV",
        "CINF",
        "AFL",
        "AIG",
        "XL",
        "MBG",
    ],
}


class CompsAnalyzer:
    """
    可比公司分析器

    基于目标公司，筛选可比公司并计算估值指标
    """

    # 默认可比公司数量
    DEFAULT_COMPS_COUNT = 8

    def __init__(self, comps_count: int = DEFAULT_COMPS_COUNT):
        self.comps_count = comps_count

    def analyze(self, symbol: str, sector: Optional[str] = None) -> CompsResult:
        """
        执行可比公司分析

        Args:
            symbol: 目标股票代码 (如 "NVDA")
            sector: 行业分类 (可选，如 "Technology", "Semiconductors")

        Returns:
            CompsResult: 可比公司分析结果
        """
        try:
            # 获取目标公司信息
            target = self._get_company_data(symbol)
            if not target:
                return CompsResult(
                    target_symbol=symbol,
                    error=f"无法获取目标公司 {symbol} 的数据",
                )

            # 确定行业
            if not sector:
                sector = self._detect_sector(target)
            if not sector:
                sector = "Technology"  # 默认

            # 获取可比公司
            comps_symbols = self._get_comps_symbols(sector, symbol)

            # 获取可比公司数据
            comps = []
            for comp_symbol in comps_symbols:
                comp = self._get_company_data(comp_symbol)
                if comp and comp.revenue > 0:
                    comps.append(comp)

            if not comps:
                return CompsResult(
                    target_symbol=symbol,
                    target_name=target.company_name,
                    sector=sector,
                    error="无可比公司数据",
                )

            # 计算统计指标
            operating_metrics = self._calculate_operating_metrics(comps)
            valuation_multiples = self._calculate_valuation_multiples(comps)
            percentiles = self._calculate_percentiles(comps)

            # 计算目标公司隐含估值
            implied = self._calculate_implied_valuation(target, percentiles)

            # 生成建议
            recommendation = self._generate_recommendation(target, percentiles)

            return CompsResult(
                target_symbol=symbol,
                target_name=target.company_name,
                sector=sector,
                industry=target.industry,
                comps=comps,
                operating_metrics=operating_metrics,
                valuation_multiples=valuation_multiples,
                percentiles=percentiles,
                implied_pe_low=implied["pe"]["low"],
                implied_pe_mid=implied["pe"]["mid"],
                implied_pe_high=implied["pe"]["high"],
                implied_ps_low=implied["ps"]["low"],
                implied_ps_mid=implied["ps"]["mid"],
                implied_ps_high=implied["ps"]["high"],
                implied_ev_ebitda_low=implied["ev_ebitda"]["low"],
                implied_ev_ebitda_mid=implied["ev_ebitda"]["mid"],
                implied_ev_ebitda_high=implied["ev_ebitda"]["high"],
                recommendation=recommendation["rating"],
                confidence=recommendation["confidence"],
            )

        except Exception as e:
            return CompsResult(target_symbol=symbol, error=f"分析失败: {str(e)}")

    def _get_company_data(self, symbol: str) -> Optional[CompCompany]:
        """获取单个公司数据"""
        try:
            stock = yf.Ticker(symbol)
            info = stock.info

            if not info:
                return None

            # 基本信息
            company_name = info.get("longName", info.get("shortName", symbol))
            sector = info.get("sector", "")
            industry = info.get("industry", "")

            # 市值和估值
            market_cap = info.get("marketCap", 0) or 0
            if market_cap:
                market_cap = market_cap / 1e6  # 转换为百万

            enterprise_value = info.get("enterpriseValue", 0) or 0
            if enterprise_value:
                enterprise_value = enterprise_value / 1e6

            # 股价
            current_price = info.get("currentPrice", 0) or info.get("regularMarketPrice", 0) or 0

            # 运营指标
            revenue = info.get("totalRevenue", 0) or 0
            if revenue:
                revenue = revenue / 1e6  # 百万

            revenue_growth = info.get("revenueGrowth", 0) or 0

            gross_margin = info.get("grossMargins", 0) or 0
            ebitda = info.get("ebitda", 0) or 0
            if ebitda:
                ebitda = ebitda / 1e6

            # 计算 EBITDA margin
            if revenue > 0:
                ebitda_margin = ebitda / revenue if ebitda else 0
            else:
                ebitda_margin = 0

            ebit = info.get("ebit", 0) or 0
            if ebit:
                ebit = ebit / 1e6

            net_income = info.get("netIncome", 0) or 0
            if net_income:
                net_income = net_income / 1e6

            # 自由现金流 (如果没有直接数据，估算)
            fcf = info.get("freeCashflow", 0) or 0
            if fcf:
                fcf = fcf / 1e6

            # 计算 FCF margin
            if revenue > 0:
                fcf_margin = fcf / revenue if fcf else 0
            else:
                fcf_margin = 0

            # Rule of 40 (适用于SaaS)
            if revenue_growth and fcf_margin:
                rule_of_40 = (revenue_growth * 100) + (fcf_margin * 100)
            else:
                rule_of_40 = 0

            # 估值倍数
            pe_ratio = info.get("trailingPE", 0) or 0
            ps_ratio = info.get("priceToSalesTrailing12Months", 0) or 0
            pb_ratio = info.get("priceToBook", 0) or 0

            # EV 倍数
            if enterprise_value > 0 and ebitda > 0:
                ev_ebitda = enterprise_value / ebitda
            else:
                ev_ebitda = 0

            if enterprise_value > 0 and revenue > 0:
                ev_revenue = enterprise_value / revenue
            else:
                ev_revenue = 0

            if enterprise_value > 0 and fcf > 0:
                ev_fcf = enterprise_value / fcf
            else:
                ev_fcf = 0

            currency = info.get("currency", "USD")

            return CompCompany(
                symbol=symbol,
                company_name=company_name,
                sector=sector,
                industry=industry,
                market_cap=market_cap,
                enterprise_value=enterprise_value,
                current_price=current_price,
                currency=currency,
                revenue=revenue,
                revenue_growth=revenue_growth,
                gross_margin=gross_margin,
                ebitda=ebitda,
                ebitda_margin=ebitda_margin,
                ebit=ebit,
                net_income=net_income,
                fcf=fcf,
                fcf_margin=fcf_margin,
                rule_of_40=rule_of_40,
                pe_ratio=pe_ratio,
                ps_ratio=ps_ratio,
                pb_ratio=pb_ratio,
                ev_ebitda=ev_ebitda,
                ev_revenue=ev_revenue,
                ev_fcf=ev_fcf,
            )

        except Exception:
            return None

    def _detect_sector(self, company: CompCompany) -> str:
        """根据公司行业信息检测行业分类"""
        industry = company.industry.lower() if company.industry else ""
        sector = company.sector.lower() if company.sector else ""

        # 半导体
        if "semicon" in industry or "chip" in industry:
            return "Semiconductors"
        # 软件
        if "software" in industry or "application" in industry:
            return "Software"
        # 云计算
        if "cloud" in industry:
            return "Cloud Computing"
        # 互联网/电商
        if "internet" in industry or "e-commerce" in industry or "online" in industry:
            return "E-commerce"
        # 金融服务
        if "financial" in industry or "bank" in industry:
            return "Financial Services"
        # 医疗健康
        if "health" in industry or "pharma" in industry or "biotech" in industry:
            return "Healthcare"
        # 媒体
        if "media" in industry or "entertainment" in industry:
            return "Media"
        # 零售
        if "retail" in industry:
            return "Retail"
        # 科技 (默认)
        if "technology" in sector or "tech" in sector:
            return "Technology"

        return "Technology"

    def _get_comps_symbols(self, sector: str, exclude_symbol: str) -> List[str]:
        """获取可比公司列表"""
        comps = INDUSTRY_COMPS.get(sector, INDUSTRY_COMPS["Technology"])

        # 排除目标公司
        comps = [c for c in comps if c.upper() != exclude_symbol.upper()]

        return comps[: self.comps_count]

    def _calculate_operating_metrics(self, comps: List[CompCompany]) -> OperatingMetrics:
        """计算运营指标统计"""
        if not comps:
            return OperatingMetrics()

        revenues = [c.revenue for c in comps if c.revenue > 0]
        growths = [c.revenue_growth for c in comps if c.revenue_growth]
        gross_margins = [c.gross_margin for c in comps if c.gross_margin > 0]
        ebitda_margins = [c.ebitda_margin for c in comps if c.ebitda_margin > 0]
        fcf_margins = [c.fcf_margin for c in comps if c.fcf_margin > 0]

        return OperatingMetrics(
            revenue_avg=np.mean(revenues) if revenues else 0,
            revenue_median=np.median(revenues) if revenues else 0,
            growth_avg=np.mean(growths) if growths else 0,
            growth_median=np.median(growths) if growths else 0,
            gross_margin_avg=np.mean(gross_margins) if gross_margins else 0,
            gross_margin_median=np.median(gross_margins) if gross_margins else 0,
            ebitda_margin_avg=np.mean(ebitda_margins) if ebitda_margins else 0,
            ebitda_margin_median=np.median(ebitda_margins) if ebitda_margins else 0,
            fcf_margin_avg=np.mean(fcf_margins) if fcf_margins else 0,
            fcf_margin_median=np.median(fcf_margins) if fcf_margins else 0,
        )

    def _calculate_valuation_multiples(self, comps: List[CompCompany]) -> ValuationMultiples:
        """计算估值倍数统计"""
        if not comps:
            return ValuationMultiples()

        pe_ratios = [c.pe_ratio for c in comps if c.pe_ratio > 0]
        ps_ratios = [c.ps_ratio for c in comps if c.ps_ratio > 0]
        pb_ratios = [c.pb_ratio for c in comps if c.pb_ratio > 0]
        ev_ebitdas = [c.ev_ebitda for c in comps if c.ev_ebitda > 0]
        ev_revenues = [c.ev_revenue for c in comps if c.ev_revenue > 0]
        ev_fcfs = [c.ev_fcf for c in comps if c.ev_fcf > 0]

        return ValuationMultiples(
            pe_avg=np.mean(pe_ratios) if pe_ratios else 0,
            pe_median=np.median(pe_ratios) if pe_ratios else 0,
            ps_avg=np.mean(ps_ratios) if ps_ratios else 0,
            ps_median=np.median(ps_ratios) if ps_ratios else 0,
            pb_avg=np.mean(pb_ratios) if pb_ratios else 0,
            pb_median=np.median(pb_ratios) if pb_ratios else 0,
            ev_ebitda_avg=np.mean(ev_ebitdas) if ev_ebitdas else 0,
            ev_ebitda_median=np.median(ev_ebitdas) if ev_ebitdas else 0,
            ev_revenue_avg=np.mean(ev_revenues) if ev_revenues else 0,
            ev_revenue_median=np.median(ev_revenues) if ev_revenues else 0,
            ev_fcf_avg=np.mean(ev_fcfs) if ev_fcfs else 0,
            ev_fcf_median=np.median(ev_fcfs) if ev_fcfs else 0,
        )

    def _calculate_percentiles(self, comps: List[CompCompany]) -> PercentileAnalysis:
        """计算分位数分析"""
        if not comps:
            return PercentileAnalysis()

        pe_ratios = [c.pe_ratio for c in comps if c.pe_ratio > 0]
        ps_ratios = [c.ps_ratio for c in comps if c.ps_ratio > 0]
        pb_ratios = [c.pb_ratio for c in comps if c.pb_ratio > 0]
        ev_ebitdas = [c.ev_ebitda for c in comps if c.ev_ebitda > 0]
        growths = [c.revenue_growth for c in comps if c.revenue_growth]
        gross_margins = [c.gross_margin for c in comps if c.gross_margin > 0]
        ebitda_margins = [c.ebitda_margin for c in comps if c.ebitda_margin > 0]

        def get_percentiles(data: List[float]) -> tuple:
            if len(data) < 3:
                return (0, 0, 0)
            return (
                np.percentile(data, 25),
                np.percentile(data, 50),
                np.percentile(data, 75),
            )

        pe_pct = get_percentiles(pe_ratios)
        ps_pct = get_percentiles(ps_ratios)
        pb_pct = get_percentiles(pb_ratios)
        ev_ebitda_pct = get_percentiles(ev_ebitdas)
        growth_pct = get_percentiles(growths)
        gross_margin_pct = get_percentiles(gross_margins)
        ebitda_margin_pct = get_percentiles(ebitda_margins)

        return PercentileAnalysis(
            pe_25th=pe_pct[0],
            pe_50th=pe_pct[1],
            pe_75th=pe_pct[2],
            ps_25th=ps_pct[0],
            ps_50th=ps_pct[1],
            ps_75th=ps_pct[2],
            pb_25th=pb_pct[0],
            pb_50th=pb_pct[1],
            pb_75th=pb_pct[2],
            ev_ebitda_25th=ev_ebitda_pct[0],
            ev_ebitda_50th=ev_ebitda_pct[1],
            ev_ebitda_75th=ev_ebitda_pct[2],
            revenue_growth_25th=growth_pct[0],
            revenue_growth_50th=growth_pct[1],
            revenue_growth_75th=growth_pct[2],
            gross_margin_25th=gross_margin_pct[0],
            gross_margin_50th=gross_margin_pct[1],
            gross_margin_75th=gross_margin_pct[2],
            ebitda_margin_25th=ebitda_margin_pct[0],
            ebitda_margin_50th=ebitda_margin_pct[1],
            ebitda_margin_75th=ebitda_margin_pct[2],
        )

    def _calculate_implied_valuation(
        self, target: CompCompany, percentiles: PercentileAnalysis
    ) -> Dict[str, Dict[str, float]]:
        """计算目标公司隐含估值"""
        implied = {
            "pe": {"low": 0, "mid": 0, "high": 0},
            "ps": {"low": 0, "mid": 0, "high": 0},
            "ev_ebitda": {"low": 0, "mid": 0, "high": 0},
        }

        # P/E 估值
        if target.net_income and target.net_income > 0:
            implied["pe"]["low"] = target.net_income * percentiles.pe_25th
            implied["pe"]["mid"] = target.net_income * percentiles.pe_50th
            implied["pe"]["high"] = target.net_income * percentiles.pe_75th

        # P/S 估值
        if target.revenue and target.revenue > 0:
            implied["ps"]["low"] = target.revenue * percentiles.ps_25th
            implied["ps"]["mid"] = target.revenue * percentiles.ps_50th
            implied["ps"]["high"] = target.revenue * percentiles.ps_75th

        # EV/EBITDA 估值
        if target.ebitda and target.ebitda > 0:
            implied["ev_ebitda"]["low"] = target.ebitda * percentiles.ev_ebitda_25th
            implied["ev_ebitda"]["mid"] = target.ebitda * percentiles.ev_ebitda_50th
            implied["ev_ebitda"]["high"] = target.ebitda * percentiles.ev_ebitda_75th

        return implied

    def _generate_recommendation(
        self, target: CompCompany, percentiles: PercentileAnalysis
    ) -> Dict[str, str]:
        """生成投资建议"""
        # 基于多个维度评估
        score = 0
        factors = 0

        # P/E 相对估值
        if target.pe_ratio > 0 and percentiles.pe_50th > 0:
            factors += 1
            if target.pe_ratio < percentiles.pe_25th:
                score += 1  # 被低估
            elif target.pe_ratio > percentiles.pe_75th:
                score -= 1  # 被高估

        # EV/EBITDA 相对估值
        if target.ev_ebitda > 0 and percentiles.ev_ebitda_50th > 0:
            factors += 1
            if target.ev_ebitda < percentiles.ev_ebitda_25th:
                score += 1
            elif target.ev_ebitda > percentiles.ev_ebitda_75th:
                score -= 1

        # 增长率相对评估
        if target.revenue_growth and percentiles.revenue_growth_50th > 0:
            factors += 1
            if target.revenue_growth > percentiles.revenue_growth_75th:
                score += 1  # 高增长
            elif target.revenue_growth < percentiles.revenue_growth_25th:
                score -= 1

        # 确定评级
        if factors == 0:
            rating = "HOLD"
            confidence = "LOW"
        elif score >= 1:
            rating = "UNDERVALUED"
            confidence = "MEDIUM"
        elif score <= -1:
            rating = "OVERVALUED"
            confidence = "MEDIUM"
        else:
            rating = "FAIR"
            confidence = "HIGH"

        return {"rating": rating, "confidence": confidence}
