"""
NASDAQ 数据源

使用 NASDAQ API 获取美股股票列表
"""

from typing import List, Dict, Any
import requests

from .base import BaseStockDataSource


class NasdaqDataSource(BaseStockDataSource):
    """NASDAQ API 数据源"""

    SOURCE_NAME = "NASDAQ"
    API_URL = "https://api.nasdaq.com/api/screener/stocks"
    HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    def fetch_a_stocks(self) -> List[Dict[str, Any]]:
        """NASDAQ API 不支持 A 股"""
        return []

    def fetch_us_stocks(self) -> List[Dict[str, Any]]:
        """获取美股股票列表"""
        params = {"tableonly": "true", "limit": "5000", "download": "true"}
        response = requests.get(self.API_URL, params=params, headers=self.HEADERS, timeout=30)
        response.raise_for_status()

        data = response.json()
        return self._parse_response(data)

    def _parse_response(self, data: Dict) -> List[Dict[str, Any]]:
        """解析 NASDAQ API 响应"""
        stocks = []

        if "data" in data and "rows" in data["data"]:
            rows = data["data"]["rows"]
        elif "data" in data and isinstance(data["data"], list):
            rows = data["data"]
        else:
            return stocks

        for row in rows:
            symbol = str(row.get("symbol") or row.get("ticker") or "").strip()
            name = str(row.get("name") or row.get("companyName") or "").strip()
            industry = str(row.get("sector") or row.get("industry") or "").strip()

            if not symbol or not name or symbol == "nan" or name == "nan":
                continue

            stocks.append(
                {
                    "ts_code": f"{symbol}.US",
                    "symbol": symbol,
                    "name": name,
                    "area": "美国",
                    "industry": industry if industry and industry != "nan" else None,
                    "market": "美股",
                    "list_date": None,
                }
            )

        return stocks

    def is_available(self, market: str) -> bool:
        """NASDAQ API 仅支持美股"""
        return market == "美股"
