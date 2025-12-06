from fastapi import APIRouter
from typing import List, Optional

from src.service import index as service
from src.service.data_loader.stock_list import StockListService
from .schemas import (
    AnalysisReportResponse,
    StockAnalysisRequest,
    StandardResponse,
    StockListResponse,
    StockInfoResponse,
    StockSearchRequest,
)

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


@router.get(
    "/list",
    response_model=StandardResponse[StockListResponse],
    summary="获取股票列表",
    tags=["Stock List"],
)
def get_stock_list(market: Optional[str] = None, refresh: bool = False):
    """
    获取股票列表（按tushare格式返回，按日缓存）

    Args:
        market: 市场类型，可选值：'A股'、'美股'，如果为 None 则返回所有市场
        refresh: 是否强制刷新缓存

    Returns:
        StandardResponse[StockListResponse]: 股票列表（tushare格式）
    """
    try:
        if market == "A股":
            stocks = StockListService.get_a_stock_list(refresh=refresh)
        elif market == "美股":
            stocks = StockListService.get_us_stock_list(refresh=refresh)
        else:
            stocks = StockListService.get_all_stock_list()

        # 直接转换为响应格式（保持tushare格式）
        stock_responses = [
            StockInfoResponse(
                ts_code=s.get("ts_code", ""),
                symbol=s.get("symbol", ""),
                name=s.get("name", ""),
                area=s.get("area"),
                industry=s.get("industry"),
                market=s.get("market"),
                list_date=s.get("list_date"),
            )
            for s in stocks
        ]

        return StandardResponse(
            status_code=200,
            data=StockListResponse(stocks=stock_responses, total=len(stock_responses)),
            err_msg=None,
        )
    except Exception as e:
        return StandardResponse(
            status_code=500,
            data=None,
            err_msg=f"获取股票列表失败: {str(e)}",
        )


@router.post(
    "/search",
    response_model=StandardResponse[StockListResponse],
    summary="搜索股票",
    tags=["Stock List"],
)
def search_stocks(payload: StockSearchRequest):
    """
    搜索股票（从缓存列表中搜索，按tushare格式返回）

    Args:
        payload: 搜索请求，包含关键词和市场类型

    Returns:
        StandardResponse[StockListResponse]: 匹配的股票列表（tushare格式）
    """
    try:
        if not payload.keyword or not payload.keyword.strip():
            return StandardResponse(
                status_code=400,
                data=None,
                err_msg="搜索关键词不能为空",
            )

        stocks = StockListService.search_stocks(payload.keyword, payload.market)

        # 直接转换为响应格式（保持tushare格式）
        stock_responses = [
            StockInfoResponse(
                ts_code=s.get("ts_code", ""),
                symbol=s.get("symbol", ""),
                name=s.get("name", ""),
                area=s.get("area"),
                industry=s.get("industry"),
                market=s.get("market"),
                list_date=s.get("list_date"),
            )
            for s in stocks
        ]

        return StandardResponse(
            status_code=200,
            data=StockListResponse(stocks=stock_responses, total=len(stock_responses)),
            err_msg=None,
        )
    except Exception as e:
        return StandardResponse(
            status_code=500,
            data=None,
            err_msg=f"搜索股票失败: {str(e)}",
        )
