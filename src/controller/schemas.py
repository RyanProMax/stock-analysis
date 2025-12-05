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

    name: str
    category: str
    status: str
    bullish_signals: List[Dict[str, Any]]
    bearish_signals: List[Dict[str, Any]]


class AnalysisReportResponse(BaseModel):
    symbol: str
    stock_name: str | None = None
    price: float
    trend_status: str
    trend_factor: Optional[FactorDetailResponse] = None
    volatility_factor: Optional[FactorDetailResponse] = None
    momentum_factor: Optional[FactorDetailResponse] = None
    volume_factor: Optional[FactorDetailResponse] = None
    fundamental_factor: Optional[FactorDetailResponse] = None
    bullish_signals: List[Dict[str, Any]]
    bearish_signals: List[Dict[str, Any]]
    fear_greed_index: float
    fear_greed_label: str

    class Config:
        orm_mode = True
