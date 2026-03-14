# -*- coding: utf-8 -*-
"""
Excel 导出工具

提供专业的 Excel 格式化导出功能
"""

from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

from ..model import CompsResult, DCFResult

# 样式定义
HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
NUMBER_FONT = Font(size=10)
TITLE_FONT = Font(bold=True, size=14)
SUBTITLE_FONT = Font(bold=True, size=12)

POSITIVE_FILL = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
NEGATIVE_FILL = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

THIN_BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)


class CompsExcelExporter:
    """可比公司分析 Excel 导出器"""

    def export(self, result: CompsResult) -> BytesIO:
        """
        导出 Comps 分析结果到 Excel

        Args:
            result: Comps 分析结果

        Returns:
            BytesIO: Excel 文件流
        """
        wb = Workbook()

        # 创建工作表
        ws_summary = wb.active
        assert ws_summary is not None, "Failed to create worksheet"
        ws_summary.title = "Summary"

        ws_comps = wb.create_sheet("Comparable Companies")
        ws_multiples = wb.create_sheet("Valuation Multiples")
        ws_percentiles = wb.create_sheet("Percentile Analysis")

        # 填充数据
        self._fill_summary(ws_summary, result)
        self._fill_comps(ws_comps, result)
        self._fill_multiples(ws_multiples, result)
        self._fill_percentiles(ws_percentiles, result)

        # 保存到 BytesIO
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        return buffer

    def _fill_summary(self, ws, result: CompsResult):
        """填充汇总页"""
        # 标题
        ws["A1"] = "Comparable Company Analysis"
        ws["A1"].font = TITLE_FONT
        ws.merge_cells("A1:E1")

        # 目标公司信息
        ws["A3"] = "Target Company"
        ws["A3"].font = SUBTITLE_FONT

        ws["A4"] = "Symbol:"
        ws["B4"] = result.target_symbol
        ws["A5"] = "Name:"
        ws["B5"] = result.target_name
        ws["A6"] = "Sector:"
        ws["B6"] = result.sector
        ws["A7"] = "Industry:"
        ws["B7"] = result.industry

        # 分析结果
        ws["A9"] = "Analysis Summary"
        ws["A9"].font = SUBTITLE_FONT

        ws["A10"] = "Comparable Companies:"
        ws["B10"] = len(result.comps)
        ws["A11"] = "Recommendation:"
        ws["B11"] = result.recommendation
        ws["A12"] = "Confidence:"
        ws["B12"] = result.confidence

        # 隐含估值
        ws["A14"] = "Implied Valuation (Million USD)"
        ws["A14"].font = SUBTITLE_FONT

        ws["A15"] = "Method"
        ws["B15"] = "Low (25th)"
        ws["C15"] = "Mid (50th)"
        ws["D15"] = "High (75th)"

        for col in ["A", "B", "C", "D"]:
            ws[f"{col}15"].fill = HEADER_FILL
            ws[f"{col}15"].font = HEADER_FONT

        ws["A16"] = "P/E Implied"
        ws["B16"] = round(result.implied_pe_low, 2)
        ws["C16"] = round(result.implied_pe_mid, 2)
        ws["D16"] = round(result.implied_pe_high, 2)

        ws["A17"] = "P/S Implied"
        ws["B17"] = round(result.implied_ps_low, 2)
        ws["C17"] = round(result.implied_ps_mid, 2)
        ws["D17"] = round(result.implied_ps_high, 2)

        ws["A18"] = "EV/EBITDA Implied"
        ws["B18"] = round(result.implied_ev_ebitda_low, 2)
        ws["C18"] = round(result.implied_ev_ebitda_mid, 2)
        ws["D18"] = round(result.implied_ev_ebitda_high, 2)

        # 调整列宽
        ws.column_dimensions["A"].width = 25
        ws.column_dimensions["B"].width = 15
        ws.column_dimensions["C"].width = 15
        ws.column_dimensions["D"].width = 15

    def _fill_comps(self, ws, result: CompsResult):
        """填充可比公司数据"""
        # 标题
        ws["A1"] = "Comparable Companies"
        ws["A1"].font = TITLE_FONT

        # 表头
        headers = [
            "Symbol",
            "Company Name",
            "Market Cap ($M)",
            "Revenue ($M)",
            "Revenue Growth (%)",
            "Gross Margin (%)",
            "EBITDA Margin (%)",
            "FCF Margin (%)",
            "P/E",
            "P/S",
            "EV/EBITDA",
        ]

        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.fill = HEADER_FILL
            cell.font = HEADER_FONT
            cell.border = THIN_BORDER

        # 数据
        for row, comp in enumerate(result.comps, 4):
            data = [
                comp.symbol,
                comp.company_name,
                round(comp.market_cap, 2),
                round(comp.revenue, 2),
                round(comp.revenue_growth * 100, 2),
                round(comp.gross_margin * 100, 2),
                round(comp.ebitda_margin * 100, 2),
                round(comp.fcf_margin * 100, 2),
                round(comp.pe_ratio, 2) if comp.pe_ratio > 0 else "N/A",
                round(comp.ps_ratio, 2) if comp.ps_ratio > 0 else "N/A",
                round(comp.ev_ebitda, 2) if comp.ev_ebitda > 0 else "N/A",
            ]

            for col, value in enumerate(data, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.border = THIN_BORDER

                # 条件格式化 - 增长率
                if col == 5 and isinstance(value, (int, float)):
                    if value > 0:
                        cell.fill = POSITIVE_FILL
                    elif value < 0:
                        cell.fill = NEGATIVE_FILL

        # 调整列宽
        column_widths = [10, 40, 15, 15, 18, 15, 18, 15, 10, 10, 12]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width

    def _fill_multiples(self, ws, result: CompsResult):
        """填充估值倍数统计"""
        ws["A1"] = "Valuation Multiples Statistics"
        ws["A1"].font = TITLE_FONT

        # 表头
        headers = ["Metric", "Average", "Median"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.fill = HEADER_FILL
            cell.font = HEADER_FONT
            cell.border = THIN_BORDER

        # 数据
        multiples = [
            (
                "P/E",
                result.valuation_multiples.pe_avg,
                result.valuation_multiples.pe_median,
            ),
            (
                "P/S",
                result.valuation_multiples.ps_avg,
                result.valuation_multiples.ps_median,
            ),
            (
                "P/B",
                result.valuation_multiples.pb_avg,
                result.valuation_multiples.pb_median,
            ),
            (
                "EV/EBITDA",
                result.valuation_multiples.ev_ebitda_avg,
                result.valuation_multiples.ev_ebitda_median,
            ),
            (
                "EV/Revenue",
                result.valuation_multiples.ev_revenue_avg,
                result.valuation_multiples.ev_revenue_median,
            ),
            (
                "EV/FCF",
                result.valuation_multiples.ev_fcf_avg,
                result.valuation_multiples.ev_fcf_median,
            ),
        ]

        for row, (name, avg, median) in enumerate(multiples, 4):
            ws.cell(row=row, column=1, value=name).border = THIN_BORDER
            ws.cell(row=row, column=2, value=round(avg, 2)).border = THIN_BORDER
            ws.cell(row=row, column=3, value=round(median, 2)).border = THIN_BORDER

        # 调整列宽
        ws.column_dimensions["A"].width = 15
        ws.column_dimensions["B"].width = 12
        ws.column_dimensions["C"].width = 12

    def _fill_percentiles(self, ws, result: CompsResult):
        """填充分位数分析"""
        ws["A1"] = "Percentile Analysis"
        ws["A1"].font = TITLE_FONT

        # 表头
        headers = ["Metric", "25th", "50th (Median)", "75th"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.fill = HEADER_FILL
            cell.font = HEADER_FONT
            cell.border = THIN_BORDER

        # 估值倍数分位数
        ws["A4"] = "Valuation Multiples"
        ws["A4"].font = SUBTITLE_FONT

        percentiles = [
            (
                "P/E",
                result.percentiles.pe_25th,
                result.percentiles.pe_50th,
                result.percentiles.pe_75th,
            ),
            (
                "P/S",
                result.percentiles.ps_25th,
                result.percentiles.ps_50th,
                result.percentiles.ps_75th,
            ),
            (
                "P/B",
                result.percentiles.pb_25th,
                result.percentiles.pb_50th,
                result.percentiles.pb_75th,
            ),
            (
                "EV/EBITDA",
                result.percentiles.ev_ebitda_25th,
                result.percentiles.ev_ebitda_50th,
                result.percentiles.ev_ebitda_75th,
            ),
        ]

        row = 5
        for name, p25, p50, p75 in percentiles:
            ws.cell(row=row, column=1, value=name).border = THIN_BORDER
            ws.cell(row=row, column=2, value=round(p25, 2)).border = THIN_BORDER
            ws.cell(row=row, column=3, value=round(p50, 2)).border = THIN_BORDER
            ws.cell(row=row, column=4, value=round(p75, 2)).border = THIN_BORDER
            row += 1

        # 运营指标分位数
        row += 1
        ws.cell(row=row, column=1, value="Operating Metrics").font = SUBTITLE_FONT
        row += 1

        operating = [
            (
                "Revenue Growth (%)",
                result.percentiles.revenue_growth_25th * 100,
                result.percentiles.revenue_growth_50th * 100,
                result.percentiles.revenue_growth_75th * 100,
            ),
            (
                "Gross Margin (%)",
                result.percentiles.gross_margin_25th * 100,
                result.percentiles.gross_margin_50th * 100,
                result.percentiles.gross_margin_75th * 100,
            ),
            (
                "EBITDA Margin (%)",
                result.percentiles.ebitda_margin_25th * 100,
                result.percentiles.ebitda_margin_50th * 100,
                result.percentiles.ebitda_margin_75th * 100,
            ),
        ]

        for name, p25, p50, p75 in operating:
            ws.cell(row=row, column=1, value=name).border = THIN_BORDER
            ws.cell(row=row, column=2, value=round(p25, 2)).border = THIN_BORDER
            ws.cell(row=row, column=3, value=round(p50, 2)).border = THIN_BORDER
            ws.cell(row=row, column=4, value=round(p75, 2)).border = THIN_BORDER
            row += 1

        # 调整列宽
        ws.column_dimensions["A"].width = 20
        ws.column_dimensions["B"].width = 12
        ws.column_dimensions["C"].width = 15
        ws.column_dimensions["D"].width = 12


class DCFExcelExporter:
    """DCF 估值模型 Excel 导出器"""

    def export(self, result: DCFResult) -> BytesIO:
        """
        导出 DCF 估值结果到 Excel

        Args:
            result: DCF 估值结果

        Returns:
            BytesIO: Excel 文件流
        """
        wb = Workbook()

        # 创建工作表
        ws_summary = wb.active
        assert ws_summary is not None, "Failed to create worksheet"
        ws_summary.title = "Summary"

        ws_wacc = wb.create_sheet("WACC")
        ws_fcf = wb.create_sheet("FCF Projections")
        ws_terminal = wb.create_sheet("Terminal Value")
        ws_sensitivity = wb.create_sheet("Sensitivity Analysis")

        # 填充数据
        self._fill_summary(ws_summary, result)
        self._fill_wacc(ws_wacc, result)
        self._fill_fcf(ws_fcf, result)
        self._fill_terminal(ws_terminal, result)
        self._fill_sensitivity(ws_sensitivity, result)

        # 保存到 BytesIO
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        return buffer

    def _fill_summary(self, ws, result: DCFResult):
        """填充汇总页"""
        # 标题
        ws["A1"] = "DCF Valuation Analysis"
        ws["A1"].font = TITLE_FONT
        ws.merge_cells("A1:E1")

        # 公司信息
        ws["A3"] = "Company Information"
        ws["A3"].font = SUBTITLE_FONT

        ws["A4"] = "Symbol:"
        ws["B4"] = result.symbol
        ws["A5"] = "Company Name:"
        ws["B5"] = result.company_name
        ws["A6"] = "Current Price:"
        ws["B6"] = f"{result.currency} {result.current_price:.2f}"

        # 估值结果
        ws["A8"] = "Valuation Results"
        ws["A8"].font = SUBTITLE_FONT

        ws["A9"] = "Enterprise Value ($M):"
        ws["B9"] = round(result.enterprise_value, 2)
        ws["A10"] = "Equity Value ($M):"
        ws["B10"] = round(result.equity_value, 2)
        ws["A11"] = "Implied Price:"
        ws["B11"] = f"{result.currency} {result.implied_price:.2f}"
        ws["A12"] = "Upside/Downside:"
        ws["B12"] = f"{result.upside:.2f}%"

        # 评级
        ws["A14"] = "Recommendation:"
        ws["B14"] = result.recommendation
        ws["A15"] = "Confidence:"
        ws["B15"] = result.confidence

        # 估值区间
        ws["A17"] = "Valuation Range"
        ws["A17"].font = SUBTITLE_FONT

        ws["A18"] = "Bear Case:"
        ws["B18"] = f"{result.currency} {result.valuation_range.bear_case:.2f}"
        ws["A19"] = "Base Case:"
        ws["B19"] = f"{result.currency} {result.valuation_range.base_case:.2f}"
        ws["A20"] = "Bull Case:"
        ws["B20"] = f"{result.currency} {result.valuation_range.bull_case:.2f}"

        # 调整列宽
        ws.column_dimensions["A"].width = 25
        ws.column_dimensions["B"].width = 20

    def _fill_wacc(self, ws, result: DCFResult):
        """填充 WACC 计算"""
        ws["A1"] = "WACC Calculation"
        ws["A1"].font = TITLE_FONT

        wacc = result.wacc_components

        # 股权成本
        ws["A3"] = "Cost of Equity"
        ws["A3"].font = SUBTITLE_FONT
        ws["A4"] = "Risk Free Rate:"
        ws["B4"] = f"{wacc.risk_free_rate * 100:.2f}%"
        ws["A5"] = "Beta:"
        ws["B5"] = round(wacc.beta, 2)
        ws["A6"] = "Equity Risk Premium:"
        ws["B6"] = f"{wacc.equity_risk_premium * 100:.2f}%"
        ws["A7"] = "Cost of Equity:"
        ws["B7"] = f"{wacc.cost_of_equity * 100:.2f}%"

        # 债务成本
        ws["A9"] = "Cost of Debt"
        ws["A9"].font = SUBTITLE_FONT
        ws["A10"] = "Cost of Debt (Pre-tax):"
        ws["B10"] = f"{wacc.cost_of_debt * 100:.2f}%"
        ws["A11"] = "Tax Rate:"
        ws["B11"] = f"{wacc.tax_rate * 100:.2f}%"
        ws["A12"] = "Cost of Debt (After-tax):"
        ws["B12"] = f"{wacc.cost_of_debt_after_tax * 100:.2f}%"

        # 资本结构
        ws["A14"] = "Capital Structure"
        ws["A14"].font = SUBTITLE_FONT
        ws["A15"] = "Market Cap ($M):"
        ws["B15"] = round(wacc.market_cap, 2)
        ws["A16"] = "Net Debt ($M):"
        ws["B16"] = round(wacc.net_debt, 2)
        ws["A17"] = "Enterprise Value ($M):"
        ws["B17"] = round(wacc.enterprise_value, 2)
        ws["A18"] = "Equity Weight:"
        ws["B18"] = f"{wacc.equity_weight * 100:.2f}%"
        ws["A19"] = "Debt Weight:"
        ws["B19"] = f"{wacc.debt_weight * 100:.2f}%"

        # 最终 WACC
        ws["A21"] = "Weighted Average Cost of Capital (WACC)"
        ws["A21"].font = SUBTITLE_FONT
        ws["A22"] = "WACC:"
        ws["B22"] = f"{wacc.wacc * 100:.2f}%"

        ws.column_dimensions["A"].width = 30
        ws.column_dimensions["B"].width = 15

    def _fill_fcf(self, ws, result: DCFResult):
        """填充 FCF 预测"""
        ws["A1"] = "Free Cash Flow Projections"
        ws["A1"].font = TITLE_FONT

        # 表头
        headers = [
            "Year",
            "Revenue ($M)",
            "Growth",
            "EBITDA Margin",
            "FCF ($M)",
            "PV of FCF ($M)",
        ]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.fill = HEADER_FILL
            cell.font = HEADER_FONT
            cell.border = THIN_BORDER

        # 数据
        for row, fcf in enumerate(result.fcf_projections, 4):
            data = [
                f"Year {fcf.year}",
                round(fcf.revenue / 1e6, 2),
                f"{fcf.revenue_growth * 100:.1f}%",
                f"{fcf.ebitda_margin * 100:.1f}%",
                round(fcf.fcf / 1e6, 2),
                round(fcf.pv_fcf / 1e6, 2),
            ]
            for col, value in enumerate(data, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.border = THIN_BORDER

        # 合计
        row = len(result.fcf_projections) + 4
        ws.cell(row=row, column=1, value="Total PV of FCF").font = SUBTITLE_FONT
        ws.cell(row=row, column=5, value=round(result.pv_fcf_sum, 2)).border = THIN_BORDER

        ws.column_dimensions["A"].width = 12
        ws.column_dimensions["B"].width = 18
        ws.column_dimensions["C"].width = 12
        ws.column_dimensions["D"].width = 15
        ws.column_dimensions["E"].width = 15
        ws.column_dimensions["F"].width = 18

    def _fill_terminal(self, ws, result: DCFResult):
        """填充终值计算"""
        ws["A1"] = "Terminal Value Calculation"
        ws["A1"].font = TITLE_FONT

        tv = result.terminal_value

        ws["A3"] = "Terminal Value"
        ws["A3"].font = SUBTITLE_FONT
        ws["A4"] = "Terminal FCF ($M):"
        ws["B4"] = round(tv.terminal_fcf / 1e6, 2)
        ws["A5"] = "Terminal Growth Rate:"
        ws["B5"] = f"{tv.terminal_growth_rate * 100:.2f}%"
        ws["A6"] = "Exit Multiple:"
        ws["B6"] = f"{tv.exit_multiple:.1f}x"
        ws["A7"] = "Terminal Value ($M):"
        ws["B7"] = round(tv.terminal_value / 1e6, 2)
        ws["A8"] = "PV of Terminal Value ($M):"
        ws["B8"] = round(tv.pv_terminal / 1e6, 2)
        ws["A9"] = "Terminal Value % of EV:"
        ws["B9"] = f"{tv.terminal_value_pct * 100:.1f}%"

        ws.column_dimensions["A"].width = 30
        ws.column_dimensions["B"].width = 20

    def _fill_sensitivity(self, ws, result: DCFResult):
        """填充敏感性分析"""
        ws["A1"] = "Sensitivity Analysis - 75 Cell Matrix"
        ws["A1"].font = TITLE_FONT

        sens = result.sensitivity

        # 矩阵1: WACC vs Terminal Growth Rate
        ws["A3"] = "1. WACC vs Terminal Growth Rate"
        ws["A3"].font = SUBTITLE_FONT

        # 表头
        headers = ["WACC \\ Growth"] + [f"{g*100:.1f}%" for g in sens.terminal_growth_values]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col, value=header)
            cell.fill = HEADER_FILL
            cell.font = HEADER_FONT
            cell.border = THIN_BORDER

        # 数据
        for row_idx, wacc_val in enumerate(sens.wacc_values):
            ws.cell(row=5 + row_idx, column=1, value=f"{wacc_val * 100:.1f}%").border = THIN_BORDER
            for col_idx, price in enumerate(sens.price_matrix_wacc_growth[row_idx]):
                cell = ws.cell(row=5 + row_idx, column=2 + col_idx, value=round(price, 2))
                cell.border = THIN_BORDER

        # 矩阵2: Revenue Growth vs EBITDA Margin
        row_offset = len(sens.wacc_values) + 7
        ws.cell(row=row_offset, column=1, value="2. Revenue Growth vs EBITDA Margin").font = (
            SUBTITLE_FONT
        )

        # 表头
        headers2 = ["Growth \\ Margin"] + [f"{m*100:.1f}%" for m in sens.ebitda_margin_values]
        for col, header in enumerate(headers2, 1):
            cell = ws.cell(row=row_offset + 1, column=col, value=header)
            cell.fill = HEADER_FILL
            cell.font = HEADER_FONT
            cell.border = THIN_BORDER

        # 数据
        for row_idx, growth_val in enumerate(sens.revenue_growth_values):
            ws.cell(
                row=row_offset + 2 + row_idx, column=1, value=f"{growth_val * 100:.1f}%"
            ).border = THIN_BORDER
            for col_idx, price in enumerate(sens.price_matrix_growth_margin[row_idx]):
                cell = ws.cell(
                    row=row_offset + 2 + row_idx,
                    column=2 + col_idx,
                    value=round(price, 2),
                )
                cell.border = THIN_BORDER

        ws.column_dimensions["A"].width = 18
        for i in range(2, 8):
            ws.column_dimensions[get_column_letter(i)].width = 12
