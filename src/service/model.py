from dataclasses import dataclass, field
import pandas as pd
from typing import List, Optional


class Config:
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    KDJ_J_OVERSOLD = 10
    KDJ_J_OVERBOUGHT = 90
    STRONG_BUY_SCORE = 80
    BUY_SCORE = 60
    NEUTRAL_SCORE = 40
    STRONG_SELL_SCORE = 20


cfg = Config()


@dataclass
class AnalysisReport:
    """封装单次完整的股票分析结果"""

    symbol: str
    stock_name: str
    price: float
    score: int
    advice: str
    trend_status: str
    stop_loss_price: float
    data_and_indicators: Optional[pd.DataFrame]
    bullish_signals: List[str] = field(default_factory=list)
    bearish_signals: List[str] = field(default_factory=list)
    fear_greed_index: float = 50.0
    fear_greed_label: str = "中性"
