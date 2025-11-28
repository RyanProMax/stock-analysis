from pydantic import BaseModel
from typing import List

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


class AnalysisReportResponse(BaseModel):
    symbol: str
    stock_name: str | None = None
    price: float
    score: int
    advice: str
    trend_status: str
    stop_loss_price: float
    bullish_signals: List[str]
    bearish_signals: List[str]
    fear_greed_index: float
    fear_greed_label: str

    class Config:
        orm_mode = True
