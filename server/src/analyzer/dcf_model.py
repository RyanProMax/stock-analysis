# -*- coding: utf-8 -*-
"""
DCF (Discounted Cash Flow) 估值模型

基于自由现金流折现法的股票估值分析
"""

import yfinance as yf
from typing import List, Tuple

from ..model import (
    DCFResult,
    WACCComponents,
    FCFProjection,
    TerminalValue,
    SensitivityMatrix,
    ValuationRange,
)


class DCFModel:
    """
    DCF 估值模型

    使用 yfinance 获取美股财务数据，计算企业价值和股权价值
    """

    # 默认��数
    DEFAULT_RISK_FREE_RATE = 0.042  # 10年期美债收益率
    DEFAULT_EQUITY_RISK_PREMIUM = 0.055  # 股权风险溢价
    DEFAULT_TAX_RATE = 0.25  # 税率
    DEFAULT_TERMINAL_GROWTH_RATE = 0.025  # 永续增长率
    DEFAULT_PROJECTION_YEARS = 5  # 预测年限

    # 敏感性分析范围 (5×5 = 25格)
    WACC_RANGE = [-0.02, -0.01, 0, 0.01, 0.02]  # WACC 变动范围
    TERMINAL_GROWTH_RANGE = [-0.01, -0.005, 0, 0.005, 0.01]  # 终值增长率变动范围
    REVENUE_GROWTH_RANGE = [-0.05, -0.025, 0, 0.025, 0.05]  # 营收增长率变动范围
    EBITDA_MARGIN_RANGE = [-0.05, -0.025, 0, 0.025, 0.05]  # EBITDA 利润率变动范围
    EXIT_MULTIPLE_RANGE = [-3, -1.5, 0, 1.5, 3]  # 退出倍数变动范围 (基于 EV/EBITDA)

    def __init__(
        self,
        risk_free_rate: float = DEFAULT_RISK_FREE_RATE,
        equity_risk_premium: float = DEFAULT_EQUITY_RISK_PREMIUM,
        tax_rate: float = DEFAULT_TAX_RATE,
        terminal_growth_rate: float = DEFAULT_TERMINAL_GROWTH_RATE,
        projection_years: int = DEFAULT_PROJECTION_YEARS,
    ):
        self.risk_free_rate = risk_free_rate
        self.equity_risk_premium = equity_risk_premium
        self.tax_rate = tax_rate
        self.terminal_growth_rate = terminal_growth_rate
        self.projection_years = projection_years

    def analyze(self, symbol: str) -> DCFResult:
        """
        执行 DCF 估值分析

        Args:
            symbol: 股票代码 (如 "NVDA", "AAPL")

        Returns:
            DCFResult: DCF 估值结果
        """
        try:
            # 获取股票数据
            stock = yf.Ticker(symbol)
            info = stock.info

            if not info:
                return DCFResult(symbol=symbol, error="无法获取股票数据")

            # 基本信息
            company_name = info.get("longName", info.get("shortName", symbol))
            current_price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
            currency = info.get("currency", "USD")

            # 1. 计算 WACC
            wacc_components = self._calculate_wacc(info)

            if wacc_components.wacc <= 0:
                return DCFResult(
                    symbol=symbol,
                    company_name=company_name,
                    current_price=current_price,
                    currency=currency,
                    error="WACC 计算失败，数据不完整",
                )

            # 2. 获取历史财务数据用于预测
            historical_fcf = self._get_historical_fcf(info)

            if not historical_fcf or historical_fcf[-1] <= 0:
                return DCFResult(
                    symbol=symbol,
                    company_name=company_name,
                    current_price=current_price,
                    currency=currency,
                    wacc_components=wacc_components,
                    error="无法获取有效的自由现金流数据",
                )

            # 3. 预测未来 FCF
            fcf_projections = self._project_fcf(historical_fcf, info, wacc_components.wacc)

            # 4. 计算终值
            terminal_value = self._calculate_terminal_value(fcf_projections, wacc_components.wacc)

            # 5. 计算企业价值
            pv_fcf_sum = sum(p.pv_fcf for p in fcf_projections)
            enterprise_value = pv_fcf_sum + terminal_value.pv_terminal

            # 6. 计算股权价值
            net_debt = self._get_net_debt(info)
            equity_value = enterprise_value - net_debt

            # 7. 计算隐含股价
            shares_outstanding = info.get("sharesOutstanding", 0)
            if shares_outstanding > 0:
                implied_price = equity_value / shares_outstanding
            else:
                implied_price = 0

            # 8. 计算上涨空间
            if current_price > 0:
                upside = ((implied_price - current_price) / current_price) * 100
            else:
                upside = 0

            # 9. 敏感性分析 (75格矩阵)
            sensitivity = self._build_sensitivity_matrices(
                fcf_projections,
                wacc_components.wacc,
                self.terminal_growth_rate,
                net_debt,
                shares_outstanding,
                info,
            )

            # 10. 估值区间
            valuation_range = self._calculate_valuation_range(sensitivity)

            # 11. 生成评级
            recommendation, confidence = self._generate_recommendation(upside, info)

            result = DCFResult(
                symbol=symbol,
                company_name=company_name,
                current_price=current_price,
                currency=currency,
                enterprise_value=enterprise_value / 1e6,  # 转换为百万
                equity_value=equity_value / 1e6,
                implied_price=implied_price,
                upside=upside,
                wacc_components=wacc_components,
                fcf_projections=fcf_projections,
                terminal_value=terminal_value,
                pv_fcf_sum=pv_fcf_sum / 1e6,
                pv_terminal=terminal_value.pv_terminal / 1e6,
                sensitivity=sensitivity,
                valuation_range=valuation_range,
                recommendation=recommendation,
                confidence=confidence,
                assumptions={
                    "risk_free_rate": self.risk_free_rate,
                    "equity_risk_premium": self.equity_risk_premium,
                    "tax_rate": self.tax_rate,
                    "terminal_growth_rate": self.terminal_growth_rate,
                    "projection_years": self.projection_years,
                },
            )

            return result

        except Exception as e:
            return DCFResult(symbol=symbol, error=f"DCF 分析异常: {str(e)}")

    def _calculate_wacc(self, info: dict) -> WACCComponents:
        """计算加权平均资本成本 (WACC)"""
        components = WACCComponents(
            risk_free_rate=self.risk_free_rate,
            equity_risk_premium=self.equity_risk_premium,
            tax_rate=self.tax_rate,
        )

        # Beta 系数
        beta = info.get("beta", 1.0)
        if beta is None or beta <= 0:
            beta = 1.0
        components.beta = beta

        # 股权成本 (CAPM)
        components.cost_of_equity = self.risk_free_rate + beta * self.equity_risk_premium

        # 市值
        market_cap = info.get("marketCap", 0)
        components.market_cap = market_cap

        # 债务数据
        total_debt = info.get("totalDebt", 0) or 0
        cash = info.get("totalCash", 0) or 0
        net_debt = total_debt - cash
        components.net_debt = net_debt

        # 企业价值
        enterprise_value = market_cap + net_debt
        components.enterprise_value = enterprise_value

        # 资本结构权重
        if enterprise_value > 0:
            components.equity_weight = market_cap / enterprise_value
            components.debt_weight = net_debt / enterprise_value
        else:
            components.equity_weight = 1.0
            components.debt_weight = 0.0

        # 债务成本（使用利息费用估算）
        interest_expense = info.get("interestExpense", 0) or 0
        if total_debt > 0 and interest_expense != 0:
            components.cost_of_debt = abs(interest_expense) / total_debt
        else:
            # 默认债务成本
            components.cost_of_debt = self.risk_free_rate + 0.02

        # 税后债务成本
        components.cost_of_debt_after_tax = components.cost_of_debt * (1 - self.tax_rate)

        # WACC
        components.wacc = (
            components.equity_weight * components.cost_of_equity
            + components.debt_weight * components.cost_of_debt_after_tax
        )

        return components

    def _get_historical_fcf(self, info: dict) -> List[float]:
        """获取历史自由现金流"""
        # 优先使用 yfinance 提供的 FCF
        free_cashflow = info.get("freeCashflow", 0) or 0

        if free_cashflow > 0:
            # 如果有 FCF 数据，假设过去几年按一定增长率增长
            # 使用营收增长率估算历史 FCF
            revenue_growth = info.get("revenueGrowth", 0.1) or 0.1
            growth_rate = min(revenue_growth, 0.3)  # 限制最大增长率

            historical = []
            for i in range(3):
                historical.insert(0, free_cashflow / ((1 + growth_rate) ** (i + 1)))
            historical.append(free_cashflow)
            return historical

        # 备选方案：从现金流计算
        operating_cashflow = info.get("operatingCashflow", 0) or 0
        capex = info.get("capitalExpenditures", 0) or 0

        if operating_cashflow > 0:
            calculated_fcf = operating_cashflow - abs(capex)
            if calculated_fcf > 0:
                return [calculated_fcf]

        return []

    def _project_fcf(
        self,
        historical_fcf: List[float],
        info: dict,
        wacc: float,
    ) -> List[FCFProjection]:
        """预测未来自由现金流"""
        projections = []

        # 基础数据
        base_fcf = historical_fcf[-1]
        base_revenue = info.get("totalRevenue", base_fcf * 10) or base_fcf * 10
        ebitda = info.get("ebitda", base_revenue * 0.25) or base_revenue * 0.25
        ebitda_margin = ebitda / base_revenue if base_revenue > 0 else 0.25

        # 增长率假设
        revenue_growth = info.get("revenueGrowth", 0.1) or 0.1
        # 逐步递减增长率
        growth_rates = [
            revenue_growth,
            revenue_growth * 0.9,
            revenue_growth * 0.8,
            revenue_growth * 0.7,
            revenue_growth * 0.6,
        ][: self.projection_years]

        # 折旧摊销率 (假设为营收的 5%)
        da_rate = 0.05
        # 资本支出率 (假设为营收的 7%)
        capex_rate = 0.07
        # 营运资本变化率 (假设为营收的 1%)
        nwc_rate = 0.01

        current_revenue = base_revenue
        # current_fcf = base_fcf

        for year in range(1, self.projection_years + 1):
            growth = growth_rates[year - 1]
            current_revenue = current_revenue * (1 + growth)

            # EBITDA
            year_ebitda = current_revenue * ebitda_margin

            # EBIT (假设 D&A 占 EBITDA 的 20%)
            da = current_revenue * da_rate
            year_ebit = year_ebitda - da

            # NOPAT
            nopat = year_ebit * (1 - self.tax_rate)

            # CapEx
            capex = current_revenue * capex_rate

            # 营运资本变化
            delta_nwc = current_revenue * nwc_rate

            # FCF
            year_fcf = nopat + da - capex - delta_nwc

            # 折现因子
            discount_factor = 1 / ((1 + wacc) ** year)

            # FCF 现值
            pv_fcf = year_fcf * discount_factor

            projections.append(
                FCFProjection(
                    year=year,
                    revenue=current_revenue,
                    revenue_growth=growth,
                    ebitda=year_ebitda,
                    ebitda_margin=ebitda_margin,
                    ebit=year_ebit,
                    tax_rate=self.tax_rate,
                    nopat=nopat,
                    da=da,
                    capex=capex,
                    delta_nwc=delta_nwc,
                    fcf=year_fcf,
                    discount_factor=discount_factor,
                    pv_fcf=pv_fcf,
                )
            )

            # current_fcf = year_fcf

        return projections

    def _calculate_terminal_value(
        self,
        projections: List[FCFProjection],
        wacc: float,
    ) -> TerminalValue:
        """计算终值"""
        if not projections:
            return TerminalValue()

        # 终期 FCF
        terminal_fcf = projections[-1].fcf * (1 + self.terminal_growth_rate)

        # 终值 (永续增长模型)
        terminal_value = terminal_fcf / (wacc - self.terminal_growth_rate)

        # 终值现值
        pv_terminal = terminal_value / ((1 + wacc) ** self.projection_years)

        # 终值占比
        total_value = sum(p.pv_fcf for p in projections) + pv_terminal
        terminal_value_pct = (pv_terminal / total_value * 100) if total_value > 0 else 0

        return TerminalValue(
            terminal_fcf=terminal_fcf,
            terminal_growth_rate=self.terminal_growth_rate,
            terminal_value=terminal_value,
            pv_terminal=pv_terminal,
            terminal_value_pct=terminal_value_pct,
        )

    def _get_net_debt(self, info: dict) -> float:
        """获取净债务"""
        total_debt = info.get("totalDebt", 0) or 0
        cash = info.get("totalCash", 0) or 0
        return total_debt - cash

    def _build_sensitivity_matrices(
        self,
        projections: List[FCFProjection],
        base_wacc: float,
        base_terminal_growth: float,
        net_debt: float,
        shares_outstanding: float,
        info: dict,
    ) -> SensitivityMatrix:
        """
        构建3个敏感性分析矩阵 (共75格)

        矩阵1: WACC vs Terminal Growth Rate (5×5)
        矩阵2: Revenue Growth vs EBITDA Margin (5×5)
        矩阵3: Exit Multiple vs WACC (5×5)
        """
        if not projections or shares_outstanding <= 0:
            return SensitivityMatrix()

        # 获取基础数据
        base_revenue_growth = info.get("revenueGrowth", 0.1) or 0.1
        ebitda = info.get("ebitda", 0) or 0
        base_revenue = info.get("totalRevenue", 0) or 0
        base_ebitda_margin = ebitda / base_revenue if base_revenue > 0 else 0.25

        # 计算 EV/EBITDA 倍数作为退出倍数基准
        market_cap = info.get("marketCap", 0) or 0
        enterprise_value = market_cap + net_debt
        base_exit_multiple = enterprise_value / ebitda if ebitda > 0 else 15

        # ========== 矩阵1: WACC vs Terminal Growth Rate ==========
        wacc_values = [base_wacc + d for d in self.WACC_RANGE]
        terminal_growth_values = [base_terminal_growth + d for d in self.TERMINAL_GROWTH_RANGE]

        price_matrix_wacc_growth = []
        for wacc in wacc_values:
            row = []
            for growth in terminal_growth_values:
                price = self._calculate_price_with_wacc_growth(
                    projections, wacc, growth, net_debt, shares_outstanding
                )
                row.append(price)
            price_matrix_wacc_growth.append(row)

        # ========== 矩阵2: Revenue Growth vs EBITDA Margin ==========
        revenue_growth_values = [base_revenue_growth + d for d in self.REVENUE_GROWTH_RANGE]
        ebitda_margin_values = [base_ebitda_margin + d for d in self.EBITDA_MARGIN_RANGE]

        price_matrix_growth_margin = []
        for rev_growth in revenue_growth_values:
            row = []
            for ebitda_margin in ebitda_margin_values:
                price = self._calculate_price_with_growth_margin(
                    projections,
                    rev_growth,
                    ebitda_margin,
                    base_wacc,
                    base_terminal_growth,
                    net_debt,
                    shares_outstanding,
                    info,
                )
                row.append(price)
            price_matrix_growth_margin.append(row)

        # ========== 矩阵3: Exit Multiple vs WACC ==========
        exit_multiple_values = [base_exit_multiple + d for d in self.EXIT_MULTIPLE_RANGE]
        wacc_values_2 = [base_wacc + d for d in self.WACC_RANGE]

        price_matrix_multiple_wacc = []
        for exit_multiple in exit_multiple_values:
            row = []
            for wacc in wacc_values_2:
                price = self._calculate_price_with_exit_multiple(
                    projections, exit_multiple, wacc, net_debt, shares_outstanding
                )
                row.append(price)
            price_matrix_multiple_wacc.append(row)

        return SensitivityMatrix(
            # 矩阵1
            wacc_values=wacc_values,
            terminal_growth_values=terminal_growth_values,
            price_matrix_wacc_growth=price_matrix_wacc_growth,
            # 矩阵2
            revenue_growth_values=revenue_growth_values,
            ebitda_margin_values=ebitda_margin_values,
            price_matrix_growth_margin=price_matrix_growth_margin,
            # 矩阵3
            exit_multiple_values=exit_multiple_values,
            wacc_values_2=wacc_values_2,
            price_matrix_multiple_wacc=price_matrix_multiple_wacc,
        )

    def _calculate_price_with_wacc_growth(
        self,
        projections: List[FCFProjection],
        wacc: float,
        terminal_growth: float,
        net_debt: float,
        shares_outstanding: float,
    ) -> float:
        """使用给定 WACC 和终值增长率计算股价"""
        if wacc <= terminal_growth or wacc <= 0:
            return 0.0

        # 重新计算终值
        terminal_fcf = projections[-1].fcf * (1 + terminal_growth)
        terminal_value = terminal_fcf / (wacc - terminal_growth)
        pv_terminal = terminal_value / ((1 + wacc) ** self.projection_years)

        # 重新计算 FCF 现值
        pv_fcf_sum = sum(p.fcf / ((1 + wacc) ** p.year) for p in projections)

        # 企业价值和股权价值
        enterprise_value = pv_fcf_sum + pv_terminal
        equity_value = enterprise_value - net_debt

        return round(equity_value / shares_outstanding, 2) if shares_outstanding > 0 else 0.0

    def _calculate_price_with_growth_margin(
        self,
        projections: List[FCFProjection],
        revenue_growth: float,
        ebitda_margin: float,
        wacc: float,
        terminal_growth: float,
        net_debt: float,
        shares_outstanding: float,
        info: dict,
    ) -> float:
        """使用给定营收增长率和 EBITDA 利润率计算股价"""
        if wacc <= terminal_growth or wacc <= 0:
            return 0.0

        base_revenue = info.get("totalRevenue", 0) or projections[0].revenue / (
            1 + projections[0].revenue_growth
        )
        tax_rate = self.tax_rate

        # 重新预测 FCF
        current_revenue = base_revenue
        pv_fcf_sum = 0

        for year in range(1, self.projection_years + 1):
            # 增长率逐年递减
            year_growth = revenue_growth * (1 - 0.1 * (year - 1))
            current_revenue = current_revenue * (1 + year_growth)

            # EBITDA 和 FCF
            year_ebitda = current_revenue * ebitda_margin
            da = current_revenue * 0.05  # 折旧摊销率
            year_ebit = year_ebitda - da
            nopat = year_ebit * (1 - tax_rate)
            capex = current_revenue * 0.07  # 资本支出率
            delta_nwc = current_revenue * 0.01  # 营运资本变化

            year_fcf = nopat + da - capex - delta_nwc
            pv_fcf_sum += year_fcf / ((1 + wacc) ** year)

        # 终值
        terminal_fcf = year_fcf * (1 + terminal_growth)
        terminal_value = terminal_fcf / (wacc - terminal_growth)
        pv_terminal = terminal_value / ((1 + wacc) ** self.projection_years)

        # 企业价值和股权价值
        enterprise_value = pv_fcf_sum + pv_terminal
        equity_value = enterprise_value - net_debt

        return round(equity_value / shares_outstanding, 2) if shares_outstanding > 0 else 0.0

    def _calculate_price_with_exit_multiple(
        self,
        projections: List[FCFProjection],
        exit_multiple: float,
        wacc: float,
        net_debt: float,
        shares_outstanding: float,
    ) -> float:
        """使用退出倍数法计算股价"""
        if exit_multiple <= 0 or wacc <= 0:
            return 0.0

        # 使用退出倍数计算终值
        terminal_ebitda = projections[-1].ebitda
        terminal_value = terminal_ebitda * exit_multiple
        pv_terminal = terminal_value / ((1 + wacc) ** self.projection_years)

        # 重新计算 FCF 现值
        pv_fcf_sum = sum(p.fcf / ((1 + wacc) ** p.year) for p in projections)

        # 企业价值和股权价值
        enterprise_value = pv_fcf_sum + pv_terminal
        equity_value = enterprise_value - net_debt

        return round(equity_value / shares_outstanding, 2) if shares_outstanding > 0 else 0.0

    def _calculate_valuation_range(self, sensitivity: SensitivityMatrix) -> ValuationRange:
        """根据敏感性分析 (75格矩阵) 计算估值区间"""
        # 收集所有三个矩阵的有效价格
        all_prices = []

        # 矩阵1: WACC vs Terminal Growth
        for row in sensitivity.price_matrix_wacc_growth:
            all_prices.extend([p for p in row if p > 0])

        # 矩阵2: Revenue Growth vs EBITDA Margin
        for row in sensitivity.price_matrix_growth_margin:
            all_prices.extend([p for p in row if p > 0])

        # 矩阵3: Exit Multiple vs WACC
        for row in sensitivity.price_matrix_multiple_wacc:
            all_prices.extend([p for p in row if p > 0])

        if not all_prices:
            return ValuationRange()

        # 计算统计量
        sorted_prices = sorted(all_prices)
        n = len(sorted_prices)

        bear_case = sorted_prices[int(n * 0.25)]  # 25分位数
        base_case = sorted_prices[int(n * 0.5)]  # 中位数
        bull_case = sorted_prices[int(n * 0.75)]  # 75分位数

        return ValuationRange(
            bear_case=bear_case,
            base_case=base_case,
            bull_case=bull_case,
            low=sorted_prices[0],
            mid=base_case,
            high=sorted_prices[-1],
        )

    def _generate_recommendation(
        self,
        upside: float,
        info: dict,
    ) -> Tuple[str, str]:
        """生成投资建议"""
        # 基于上涨空间判断
        if upside > 30:
            recommendation = "BUY"
        elif upside > 10:
            recommendation = "BUY"
        elif upside > -10:
            recommendation = "HOLD"
        else:
            recommendation = "SELL"

        # 置信度判断
        # 基于数据完整性和分析师一致性
        analyst_count = info.get("numberOfAnalystOpinions", 0) or 0

        if analyst_count >= 10:
            confidence = "HIGH"
        elif analyst_count >= 5:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        return recommendation, confidence
