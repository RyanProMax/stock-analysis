"""
股票分析控制器 - 处理传统股票分析接口
"""

from fastapi import APIRouter
from typing import List, Optional, Any
from dataclasses import asdict

from ...core.pipeline import stock_service
from ..schemas import (
    AnalysisReportResponse,
    StockAnalysisRequest,
    StandardResponse,
    StockListResponse,
    StockInfoResponse,
    StockSearchRequest,
)
from ...analyzer.trend_models import TrendAnalysisResult

router = APIRouter()


def _convert_trend_analysis(trend: TrendAnalysisResult | None) -> dict[str, Any] | None:
    """将趋势分析结果转换为可序列化的字典"""
    if trend is None:
        return None
    return {
        "code": trend.code,
        "trend_status": trend.trend_status.value,
        "ma_alignment": trend.ma_alignment,
        "trend_strength": trend.trend_strength,
        "ma5": trend.ma5,
        "ma10": trend.ma10,
        "ma20": trend.ma20,
        "ma60": trend.ma60,
        "current_price": trend.current_price,
        "bias_ma5": trend.bias_ma5,
        "bias_ma10": trend.bias_ma10,
        "bias_ma20": trend.bias_ma20,
        "volume_status": trend.volume_status.value,
        "volume_ratio_5d": trend.volume_ratio_5d,
        "volume_trend": trend.volume_trend,
        "support_ma5": trend.support_ma5,
        "support_ma10": trend.support_ma10,
        "resistance_levels": trend.resistance_levels,
        "support_levels": trend.support_levels,
        "macd_dif": trend.macd_dif,
        "macd_dea": trend.macd_dea,
        "macd_bar": trend.macd_bar,
        "macd_status": trend.macd_status.value,
        "macd_signal": trend.macd_signal,
        "rsi_6": trend.rsi_6,
        "rsi_12": trend.rsi_12,
        "rsi_24": trend.rsi_24,
        "rsi_status": trend.rsi_status.value,
        "rsi_signal": trend.rsi_signal,
        "buy_signal": trend.buy_signal.value,
        "signal_score": trend.signal_score,
        "signal_reasons": trend.signal_reasons,
        "risk_factors": trend.risk_factors,
    }


def _convert_report_to_response(report: Any) -> AnalysisReportResponse:
    """将 AnalysisReport 转换为 API 响应格式"""
    # 基础转换
    report_dict = asdict(report)

    # 处理趋势分析的特殊序列化
    if hasattr(report, "trend_analysis") and report.trend_analysis is not None:
        report_dict["trend_analysis"] = _convert_trend_analysis(report.trend_analysis)
    else:
        report_dict["trend_analysis"] = None

    return AnalysisReportResponse(**report_dict)


@router.post(
    "/analyze",
    response_model=StandardResponse[List[AnalysisReportResponse]],
    summary="批量分析股票列表",
    tags=["Stock Analysis"],
)
def analyze_stocks(payload: StockAnalysisRequest):
    """
    根据传入的股票代码列表执行批量分析，返回成功分析的结果列表。

    Args:
        payload: 包含股票代码列表和是否包含 Qlib 158 因子的标志
    """
    try:
        normalized = [symbol.strip().upper() for symbol in payload.symbols if symbol.strip()]
        if not normalized:
            return StandardResponse(
                status_code=400,
                data=None,
                err_msg="请至少提供一个有效的股票代码。",
            )

        reports = stock_service.batch_analyze(
            normalized, include_qlib_factors=payload.include_qlib_factors
        )
        if not reports:
            return StandardResponse(
                status_code=404,
                data=None,
                err_msg="无法获取任何股票的数据，请确认代码是否有效。",
            )

        # 转换报告为响应格式（处理特殊序列化需求）
        response_reports = [_convert_report_to_response(r) for r in reports]

        return StandardResponse(
            status_code=200,
            data=response_reports,
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
        stocks = stock_service.get_stock_list(market, refresh)

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

        stocks = stock_service.search_stocks(payload.keyword, payload.market)

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
