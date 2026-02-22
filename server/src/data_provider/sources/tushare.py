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

from ..base import BaseStockDataSource


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
            setattr(cls._pro, "_DataApi__token", cls.TOKEN)
            setattr(cls._pro, "_DataApi__http_url", "http://5k1a.xiximiao.com/dataapi")
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

    @classmethod
    def get_cn_financial_data(cls, symbol: str) -> tuple[Optional[dict], dict]:
        """
        使用 Tushare Pro 获取A股财务数据

        Args:
            symbol: A股代码（6位，如 600519）

        Returns:
            (财务数据字典, 原始数据字典)
        """
        financial_data = {}
        raw_data = {}

        pro = cls.get_pro()
        if pro is None:
            return None, raw_data

        try:
            # Tushare 需要带交易所前缀的股票代码
            ts_symbol = f"{symbol}.SH" if symbol.startswith("6") else f"{symbol}.SZ"

            # 获取估值指标 (PE/PB)
            try:
                df_basic = pro.daily_basic(
                    ts_code=ts_symbol, fields="ts_code,trade_date,pe,pe_ttm,pb"
                )
                if df_basic is not None and not df_basic.empty:
                    raw_data["daily_basic"] = df_basic.iloc[0].to_dict()
                    latest = df_basic.iloc[0]
                    # 优先使用市盈率TTM
                    if pd.notna(latest.get("pe_ttm")) and latest["pe_ttm"] > 0:
                        financial_data["pe_ratio"] = float(latest["pe_ttm"])
                    elif pd.notna(latest.get("pe")) and latest["pe"] > 0:
                        financial_data["pe_ratio"] = float(latest["pe"])
                    # 市净率
                    if pd.notna(latest.get("pb")) and latest["pb"] > 0:
                        financial_data["pb_ratio"] = float(latest["pb"])
            except Exception as e:
                print(f"⚠️ 获取估值指标失败: {e}")

            # 获取财务指标 (ROE/资产负债率)
            try:
                df_indicator = pro.fina_indicator(
                    ts_code=ts_symbol,
                    fields="ts_code,ann_date,end_date,roe,debt_to_assets",
                )
                if df_indicator is not None and not df_indicator.empty:
                    raw_data["fina_indicator"] = df_indicator.iloc[0].to_dict()
                    latest = df_indicator.iloc[0]
                    # ROE（净资产收益率）
                    if pd.notna(latest.get("roe")):
                        financial_data["roe"] = float(latest["roe"])
                    # 资产负债率
                    if pd.notna(latest.get("debt_to_assets")):
                        financial_data["debt_ratio"] = float(latest["debt_to_assets"])
            except Exception as e:
                print(f"⚠️ 获取财务指标失败: {e}")

            # 获取利润表用于计算营收增长率
            try:
                df_income = pro.income(
                    ts_code=ts_symbol, fields="ts_code,ann_date,end_date,revenue"
                )
                if df_income is not None and not df_income.empty:
                    raw_data["income"] = df_income.head(2).to_dict("records")
                    # 计算营收增长率
                    if len(df_income) >= 2:
                        latest_revenue = df_income.iloc[0].get("revenue")
                        prev_revenue = df_income.iloc[1].get("revenue")
                        if pd.notna(latest_revenue) and pd.notna(prev_revenue) and prev_revenue > 0:
                            revenue_growth = ((latest_revenue - prev_revenue) / prev_revenue) * 100
                            financial_data["revenue_growth"] = float(revenue_growth)
            except Exception as e:
                print(f"⚠️ 获取利润表失败: {e}")

        except Exception as e:
            import traceback

            print(f"❌ Tushare获取A股财务数据失败: {e}")
            traceback.print_exc()

        return financial_data if financial_data else None, raw_data
