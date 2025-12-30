"""
Tushare 数据源

使用 Tushare API 获取 A 股和美股股票列表、A股日线数据
"""

import os
from dotenv import load_dotenv
from typing import List, Dict, Any, ClassVar, Optional
import pandas as pd
import tushare as ts

load_dotenv()

from .base import BaseStockDataSource


class TushareDataSource(BaseStockDataSource):
    """Tushare 数据源"""

    SOURCE_NAME: str = "Tushare"
    TOKEN: ClassVar[str] = os.environ.get("TUSHARE_TOKEN", "")
    _pro: ClassVar[Optional[Any]] = None

    @classmethod
    def get_pro(cls) -> Optional[Any]:
        """获取 tushare pro 实例（懒加载）"""
        if cls._pro is not None:
            return cls._pro

        if not cls.TOKEN:
            return None

        try:
            cls._pro = ts.pro_api("anything")
            # 设置实际 token 和代理地址
            cls._pro._DataApi__token = cls.TOKEN
            cls._pro._DataApi__http_url = "http://5k1a.xiximiao.com/dataapi"
            print("✓ Tushare 初始化成功")
            return cls._pro
        except Exception as e:
            print(f"⚠️ Tushare 初始化失败: {e}")
            return None

    @classmethod
    def get_daily_data(cls, symbol: str) -> Optional[pd.DataFrame]:
        """
        获取 A 股日线数据

        Args:
            symbol: 股票代码（6位，如 600519）

        Returns:
            包含日线数据的 DataFrame，失败返回 None
        """
        pro = cls.get_pro()
        if pro is None:
            return None

        try:
            # Tushare 需要带交易所前缀的股票代码
            ts_symbol = f"{symbol}.SH" if symbol.startswith("6") else f"{symbol}.SZ"
            df = pro.daily(ts_code=ts_symbol, start_date="20100101")
            if df is not None and not df.empty:
                # Tushare 返回的列名是英文，需要映射
                df = df.sort_values("trade_date").reset_index(drop=True)
                df.rename(
                    columns={
                        "trade_date": "date",
                        "vol": "volume",
                    },
                    inplace=True,
                )
                # 删除不需要的列，保持与其他数据源一致
                cols_to_drop = ["ts_code", "pre_close", "change", "pct_chg"]
                for col in cols_to_drop:
                    if col in df.columns:
                        df.drop(columns=[col], inplace=True)
                return df
        except Exception as e:
            print(f"⚠️ Tushare 获取失败 [{symbol}]: {e}")

        return None

    def fetch_a_stocks(self) -> List[Dict[str, Any]]:
        """获取 A 股股票列表"""
        pro = self.get_pro()
        if pro is None:
            return []

        df = pro.stock_basic(exchange="", list_status="L")
        return self.normalize_dataframe(df)

    def fetch_us_stocks(self) -> List[Dict[str, Any]]:
        """获取美股股票列表"""
        pro = self.get_pro()
        if pro is None:
            return []

        df = pro.us_basic()
        return self.normalize_dataframe(df)

    def is_available(self, market: str) -> bool:
        """检查数据源是否可用"""
        if not self.TOKEN:
            print(f"⚠️ Tushare Token为空，跳过")
            return False
        pro = self.get_pro()
        return pro is not None
