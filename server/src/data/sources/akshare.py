"""
AkShare 数据源

使用 AkShare 获取 A 股股票列表
"""

from typing import List, Dict, Any
import akshare as ak

from .base import BaseStockDataSource


class AkShareDataSource(BaseStockDataSource):
    """AkShare 数据源"""

    SOURCE_NAME = "AkShare"

    def fetch_a_stocks(self) -> List[Dict[str, Any]]:
        """获取 A 股股票列表"""
        df = ak.stock_info_a_code_name()
        stocks = []

        for _, row in df.iterrows():
            symbol = str(row["code"]).strip()
            name = str(row["name"]).strip()

            # 根据代码判断交易所
            if symbol.startswith("6"):
                ts_code = f"{symbol}.SH"
                market = "主板"
            elif symbol.startswith("0"):
                ts_code = f"{symbol}.SZ"
                market = "主板"
            elif symbol.startswith("3"):
                ts_code = f"{symbol}.SZ"
                market = "创业板"
            else:
                ts_code = f"{symbol}.SZ"
                market = "主板"

            stocks.append(
                {
                    "ts_code": ts_code,
                    "symbol": symbol,
                    "name": name,
                    "area": None,
                    "industry": None,
                    "market": market,
                    "list_date": None,
                }
            )

        return stocks

    def fetch_us_stocks(self) -> List[Dict[str, Any]]:
        """AkShare 不支持美股"""
        return []

    def is_available(self, market: str) -> bool:
        """AkShare 仅支持 A 股"""
        return market == "A股"
