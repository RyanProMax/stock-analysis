# -*- coding: utf-8 -*-
"""
估值分析控制器 - DCF 估值接口
"""

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from typing import Optional

from ...analyzer.dcf_model import DCFModel
from ...utils.excel_exporter import DCFExcelExporter
from ..schemas import StandardResponse

router = APIRouter()

# DCF 模型实例（使用默认参数）
dcf_model = DCFModel()
dcf_exporter = DCFExcelExporter()


@router.get(
    "/dcf",
    response_model=StandardResponse[dict],
    summary="DCF 估值分析",
    tags=["Valuation"],
)
def analyze_dcf(
    symbol: str = Query(
        ...,
        description="股票代码 (仅支持美股)",
        examples=[{"description": "股票代码示例", "value": "NVDA"}],
    ),
    risk_free_rate: Optional[float] = Query(
        None,
        description="无风险利率 (默认 4.2%)",
        ge=0,
        le=0.2,
    ),
    equity_risk_premium: Optional[float] = Query(
        None,
        description="股权风险溢价 (默认 5.5%)",
        ge=0,
        le=0.2,
    ),
    terminal_growth_rate: Optional[float] = Query(
        None,
        description="永续增长率 (默认 2.5%)",
        ge=0,
        le=0.05,
    ),
):
    """
    DCF (Discounted Cash Flow) 估值分析

    基于自由现金流折现法计算股票的内在价值，包括：

    - **WACC 计算**: 加权平均资本成本（CAPM 模型）
    - **FCF 预测**: 5 年自由现金流预测
    - **终值计算**: 永续增长模型
    - **敏感性分析**: WACC vs 终值增长率的股价矩阵
    - **估值区间**: 熊市/基准/牛市情景

    仅支持美股，数据来源为 yfinance。
    """
    try:
        symbol = symbol.upper()

        # 创建自定义参数的模型实例
        model = DCFModel(
            risk_free_rate=(
                risk_free_rate if risk_free_rate is not None else DCFModel.DEFAULT_RISK_FREE_RATE
            ),
            equity_risk_premium=(
                equity_risk_premium
                if equity_risk_premium is not None
                else DCFModel.DEFAULT_EQUITY_RISK_PREMIUM
            ),
            terminal_growth_rate=(
                terminal_growth_rate
                if terminal_growth_rate is not None
                else DCFModel.DEFAULT_TERMINAL_GROWTH_RATE
            ),
        )

        # 执行 DCF 分析
        result = model.analyze(symbol)

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
            err_msg=f"DCF 分析失败: {str(e)}",
        )


@router.get(
    "/dcf/excel",
    summary="导出 DCF 估值 Excel",
    tags=["Valuation"],
)
def export_dcf_excel(
    symbol: str = Query(
        ...,
        description="股票代码 (仅支持美股)",
        examples=[{"description": "股票代码示例", "value": "NVDA"}],
    ),
    risk_free_rate: Optional[float] = Query(
        None,
        description="无风险利率 (默认 4.2%)",
        ge=0,
        le=0.2,
    ),
    equity_risk_premium: Optional[float] = Query(
        None,
        description="股权风险溢价 (默认 5.5%)",
        ge=0,
        le=0.2,
    ),
    terminal_growth_rate: Optional[float] = Query(
        None,
        description="永续增长率 (默认 2.5%)",
        ge=0,
        le=0.05,
    ),
):
    """
    导出 DCF 估值 Excel 报告

    包含以下工作表：
    - Summary: 估值汇总和评级
    - WACC: 资本成本计算
    - FCF Projections: 5年现金流预测
    - Terminal Value: 终值计算
    - Sensitivity Analysis: 75格敏感性矩阵

    返回 .xlsx 文件下载。
    """
    try:
        symbol = symbol.upper()

        # 创建自定义参数的模型实例
        model = DCFModel(
            risk_free_rate=(
                risk_free_rate if risk_free_rate is not None else DCFModel.DEFAULT_RISK_FREE_RATE
            ),
            equity_risk_premium=(
                equity_risk_premium
                if equity_risk_premium is not None
                else DCFModel.DEFAULT_EQUITY_RISK_PREMIUM
            ),
            terminal_growth_rate=(
                terminal_growth_rate
                if terminal_growth_rate is not None
                else DCFModel.DEFAULT_TERMINAL_GROWTH_RATE
            ),
        )

        # 执行 DCF 分析
        result = model.analyze(symbol)

        if result.error:
            return StandardResponse(
                status_code=400,
                data=None,
                err_msg=result.error,
            )

        # 导出 Excel
        excel_buffer = dcf_exporter.export(result)

        # 返回文件流
        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=dcf_{symbol}.xlsx"},
        )

    except Exception as e:
        return StandardResponse(
            status_code=500,
            data=None,
            err_msg=f"Excel 导出失败: {str(e)}",
        )
