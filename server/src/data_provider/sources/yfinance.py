"""
yfinance 数据源

使用 yfinance 获取美股股票列表、日线数据、财务数据
"""

from typing import List, Dict, Any, Optional
import pandas as pd

from ..base import BaseStockDataSource


class YfinanceDataSource(BaseStockDataSource):
    """yfinance 数据源"""

    SOURCE_NAME: str = "yfinance"
    priority: int = 0  # 美股优先级最高

    # 列名映射
    US_YFINANCE_MAP = {
        "Date": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
    }

    def fetch_a_stocks(self) -> List[Dict[str, Any]]:
        """yfinance 不支持 A 股列表"""
        return []

    def fetch_us_stocks(self) -> List[Dict[str, Any]]:
        """yfinance 不提供股票列表接口"""
        return []

    def is_available(self, market: str) -> bool:
        """yfinance 仅支持美股"""
        return market == "美股"

    # ==================== 日线数据实现 ====================

    def _fetch_raw_daily(self, symbol: str) -> Optional[pd.DataFrame]:
        """获取原始日线数据"""
        try:
            import yfinance as yf

            df = yf.Ticker(symbol).history(period="2y", auto_adjust=False)
            if df is not None and not df.empty:
                df = df.reset_index()
                return df
        except Exception as e:
            print(f"⚠️ yfinance 获取日线失败 [{symbol}]: {e}")
        return None

    def _normalize_daily(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """标准化日线数据"""
        df = df.copy()

        # 列名映射
        if self.US_YFINANCE_MAP:
            df.rename(columns=self.US_YFINANCE_MAP, inplace=True)

        # 统一小写
        df.columns = [c.lower() for c in df.columns]

        return df

    # ==================== 财务数据 ====================

    @classmethod
    def get_us_financial_data(cls, symbol: str) -> tuple[Optional[dict], dict]:
        """
        使用 yfinance 获取美股财务数据

        Args:
            symbol: 美股代码（如 AAPL）

        Returns:
            (财务数据字典, 原始数据字典)
            注：当前仅返回原始 info，不做字段提取
        """
        financial_data = {}
        raw_data = {}

        try:
            import yfinance as yf

            info = yf.Ticker(symbol).info
            if info and isinstance(info, dict):
                raw_data["info"] = info
                financial_data["raw_data"] = raw_data
        except Exception as e:
            print(f"⚠️ yfinance 获取美股财务数据失败 [{symbol}]: {e}")

        return financial_data if financial_data else None, raw_data
