from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# This Pydantic model defines the structure of the API response.
# It is based on the AnalysisReport dataclass but excludes non-serializable fields
# like pandas DataFrames, making it suitable for JSON output.


class StockAnalysisRequest(BaseModel):
    symbols: List[str]

    class Config:
        schema_extra = {
            "example": {
                "symbols": ["NVDA", "AAPL", "600519"],
            }
        }


class FactorDetailResponse(BaseModel):
    """因子详情响应"""

    key: str
    name: str
    category: str
    status: str
    bullish_signals: List[Dict[str, Any]]
    bearish_signals: List[Dict[str, Any]]


class FearGreedResponse(BaseModel):
    """贪恐指数响应"""

    index: float
    label: str


class AnalysisReportResponse(BaseModel):
    symbol: str
    stock_name: str | None = None
    price: float
    factors: List[FactorDetailResponse]
    fear_greed: FearGreedResponse

    class Config:
        orm_mode = True
