# -*- coding: utf-8 -*-
"""
可比公司分析控制器 - Comps Analysis
"""

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from typing import Optional

from ...analyzer.comps_analyzer import CompsAnalyzer
from ...utils.excel_exporter import CompsExcelExporter
from ..schemas import StandardResponse

router = APIRouter()

# Comps 分析器实例
comps_analyzer = CompsAnalyzer()
excel_exporter = CompsExcelExporter()


@router.get(
    "/comps",
    response_model=StandardResponse[dict],
    summary="可比公司分析",
    tags=["Valuation"],
)
def analyze_comps(
    symbol: str = Query(
        ...,
        description="股票代码 (仅支持美股)",
        examples=[{"description": "股票代码示例", "value": "NVDA"}],
    ),
    sector: Optional[str] = Query(
        None,
        description="行业分类 (可选，如 Technology, Semiconductors, Software)",
    ),
):
    """
    可比公司分析 (Comps Analysis)

    基于行业分类筛选可比公司，计算：

    - **运营指标**: 收入、增长率、毛利率、EBITDA、FCF、Rule of 40
    - **估值倍数**: P/E, P/S, EV/EBITDA, P/B, EV/FCF
    - **统计分位数**: 25th, 50th, 75th 分位数
    - **隐含估值**: 基于中位数计算的隐含股价区间

    仅支持美股，数据来源为 yfinance。
    """
    try:
        symbol = symbol.upper()

        # 执行 Comps 分析
        result = comps_analyzer.analyze(symbol, sector)

        # 转换为字典格式
        response_data = result.to_dict()

        if result.error:
            return StandardResponse(
                status_code=400,
                data=response_data,
                err_msg=result.error,
            )

        return StandardResponse(
            status_code=200,
            data=response_data,
            err_msg=None,
        )

    except Exception as e:
        return StandardResponse(
            status_code=500,
            data=None,
            err_msg=f"Comps 分析失败: {str(e)}",
        )


@router.get(
    "/comps/excel",
    summary="导出 Comps 分析 Excel",
    tags=["Valuation"],
)
def export_comps_excel(
    symbol: str = Query(
        ...,
        description="股票代码 (仅支持美股)",
        examples=[{"description": "股票代码示例", "value": "NVDA"}],
    ),
    sector: Optional[str] = Query(
        None,
        description="行业分类 (可选)",
    ),
):
    """
    导出可比公司分析 Excel 报告

    包含以下工作表：
    - Summary: 分析汇总和隐含估值
    - Comparable Companies: 可比公司详细数据
    - Valuation Multiples: 估值倍数统计
    - Percentile Analysis: 分位数分析

    返回 .xlsx 文件下载。
    """
    try:
        symbol = symbol.upper()

        # 执行 Comps 分析
        result = comps_analyzer.analyze(symbol, sector)

        if result.error:
            return StandardResponse(
                status_code=400,
                data=None,
                err_msg=result.error,
            )

        # 导出 Excel
        excel_buffer = excel_exporter.export(result)

        # 返回文件流
        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=comps_{symbol}.xlsx"},
        )

    except Exception as e:
        return StandardResponse(
            status_code=500,
            data=None,
            err_msg=f"Excel 导出失败: {str(e)}",
        )
