"""
Tushare 数据源

使用 Tushare API 获取 A 股和美股股票列表
"""

import os
from dotenv import load_dotenv
from typing import List, Dict, Any, ClassVar, Optional
import tushare as ts

load_dotenv()

from .base import BaseStockDataSource


class TushareDataSource(BaseStockDataSource):
    """Tushare 数据源"""

    SOURCE_NAME: str = "Tushare"
    TOKEN: ClassVar[str] = os.environ.get("TUSHARE_TOKEN", "")
    _pro: ClassVar[Optional[Any]] = None

    @classmethod
    def _get_pro(cls) -> Optional[Any]:
        """获取 tushare pro 实例（懒加载）"""
        if cls._pro is not None:
            return cls._pro

        if not cls.TOKEN:
            return None

        try:
            # ts.set_token(cls.TOKEN)
            cls._pro = ts.pro_api("anything")
            # your proxy
            cls._pro._DataApi__token = cls.TOKEN
            cls._pro._DataApi__http_url = "http://5k1a.xiximiao.com/dataapi"

            print("✓ Tushare 初始化成功")
            return cls._pro
        except Exception as e:
            print(f"⚠️ Tushare 初始化失败: {e}")
            return None

    def fetch_a_stocks(self) -> List[Dict[str, Any]]:
        """获取 A 股股票列表"""
        pro = self._get_pro()
        if pro is None:
            return []

        df = pro.stock_basic(exchange="", list_status="L")
        return self.normalize_dataframe(df)

    def fetch_us_stocks(self) -> List[Dict[str, Any]]:
        """获取美股股票列表"""
        pro = self._get_pro()
        if pro is None:
            return []

        df = pro.us_basic()
        return self.normalize_dataframe(df)

    def is_available(self, market: str) -> bool:
        """检查数据源是否可用"""
        if not self.TOKEN:
            print(f"⚠️ Tushare Token为空，跳过")
            return False
        pro = self._get_pro()
        return pro is not None
