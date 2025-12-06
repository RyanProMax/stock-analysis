from fastapi import APIRouter
from typing import List

from src.service import index as service
from .schemas import AnalysisReportResponse, StockAnalysisRequest, StandardResponse

router = APIRouter()


@router.post(
    "/analyze",
    response_model=StandardResponse[List[AnalysisReportResponse]],
    summary="批量分析股票列表",
    tags=["Analysis"],
)
def analyze_stocks(payload: StockAnalysisRequest):
    """
    根据传入的股票代码列表执行批量分析，返回成功分析的结果列表。
    """
    try:
        normalized = [symbol.strip().upper() for symbol in payload.symbols if symbol.strip()]
        if not normalized:
            return StandardResponse(
                status_code=400,
                data=None,
                err_msg="请至少提供一个有效的股票代码。",
            )

        reports = service.run_batch_stock_analysis(normalized)
        if not reports:
            return StandardResponse(
                status_code=404,
                data=None,
                err_msg="无法获取任何股票的数据，请确认代码是否有效。",
            )

        return StandardResponse(
            status_code=200,
            data=reports,
            err_msg=None,
        )
    except Exception as e:
        return StandardResponse(
            status_code=500,
            data=None,
            err_msg=f"服务器内部错误: {str(e)}",
        )
