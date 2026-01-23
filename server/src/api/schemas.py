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
    include_qlib_factors: bool = False  # 是否包含 Qlib 158 因子，默认 False

    class Config:
        json_schema_extra = {
            "example": {
                "symbols": ["NVDA", "AAPL", "600519"],
                "include_qlib_factors": False,
            }
        }


class FactorDetailResponse(BaseModel):
    """因子详情响应"""

    key: str
    name: str
    status: str
    bullish_signals: List[str]
    bearish_signals: List[str]
    data_source: str = ""


class FearGreedResponse(BaseModel):
    """贪恐指数响应"""

    index: float
    label: str


class FactorAnalysisResponse(BaseModel):
    """因子分析响应（技术面/基本面/Qlib）"""

    factors: List[FactorDetailResponse]
    data_source: str = ""
    raw_data: Dict[str, Any] | None


class AnalysisReportResponse(BaseModel):
    symbol: str
    stock_name: str | None = None
    price: float
    fear_greed: FearGreedResponse
    technical: FactorAnalysisResponse
    fundamental: FactorAnalysisResponse
    qlib: FactorAnalysisResponse

    class Config:
        from_attributes = True


class StockInfoResponse(BaseModel):
    """股票信息响应（tushare格式）"""

    ts_code: str  # 股票代码（带后缀，如 000001.SZ）
    symbol: str  # 股票代码（6位，如 000001）
    name: str  # 股票名称
    area: Optional[str] = None  # 地域
    industry: Optional[str] = None  # 所属行业
    market: Optional[str] = None  # 市场类型
    list_date: Optional[str] = None  # 上市日期


class StockListResponse(BaseModel):
    """股票列表响应"""

    stocks: List[StockInfoResponse]
    total: int


class StockSearchRequest(BaseModel):
    """股票搜索请求"""

    keyword: str
    market: Optional[str] = None  # "A股" 或 "美股"，None 表示搜索所有市场

    class Config:
        json_schema_extra = {
            "example": {
                "keyword": "NVDA",
                "market": None,
            }
        }
