from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Generic, TypeVar

# This Pydantic model defines the structure of the API response.
# It is based on the AnalysisReport dataclass but excludes non-serializable fields
# like pandas DataFrames, making it suitable for JSON output.

# 标准响应格式
T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    """标准API响应格式"""

    status_code: int  # HTTP状态码
    data: Optional[T] = None  # 响应数据
    err_msg: Optional[str] = None  # 错误信息

    class Config:
        json_schema_extra = {
            "example": {
                "status_code": 200,
                "data": None,
                "err_msg": None,
            }
        }


class StockAnalysisRequest(BaseModel):
    symbols: List[str]

    class Config:
        json_schema_extra = {
            "example": {
                "symbols": ["NVDA", "AAPL", "600519"],
            }
        }


class FactorDetailResponse(BaseModel):
    """因子详情响应"""

    key: str
    name: str
    status: str
    bullish_signals: List[str]
    bearish_signals: List[str]


class FearGreedResponse(BaseModel):
    """贪恐指数响应"""

    index: float
    label: str


class AnalysisReportResponse(BaseModel):
    symbol: str
    stock_name: str | None = None
    price: float
    fear_greed: FearGreedResponse
    technical_factors: List[FactorDetailResponse]
    fundamental_factors: List[FactorDetailResponse]
    qlib_factors: List[FactorDetailResponse]

    class Config:
        from_attributes = True
