"""
AkShare 数据源

使用 AkShare 获取 A 股股票列表、财务数据、日线数据
"""

from typing import List, Dict, Any, Optional, cast
import pandas as pd
import akshare as ak

from ..base import BaseStockDataSource


class AkShareDataSource(BaseStockDataSource):
    """AkShare 数据源"""

    SOURCE_NAME: str = "AkShare"
    priority: int = 1  # 优先级

    # 列名映射
    CN_EASTMONEY_MAP = {
        "日期": "date",
        "开盘": "open",
        "收盘": "close",
        "最高": "high",
        "最低": "low",
        "成交量": "volume",
        "成交额": "amount",
        "换手率": "turnover",
    }

    US_MAP = {
        "日期": "date",
        "开盘": "open",
        "最高": "high",
        "最低": "low",
        "收盘": "close",
        "成交量": "volume",
    }

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
        """AkShare 不支持美股列表"""
        return []

    def is_available(self, market: str) -> bool:
        """AkShare 支持 A 股和美股日线"""
        return market in ("A股", "美股")

    # ==================== 日线数据实现 ====================

    def _fetch_raw_daily(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        获取原始日线数据

        自动判断市场类型：
        - 纯数字 → A股
        - 包含字母 → 美股
        """
        is_us = bool(symbol.isalpha() or any(c.isalpha() for c in symbol))

        if is_us:
            return self._fetch_us_daily(symbol)
        else:
            # A股：先尝试东方财富，再尝试新浪
            df = self._fetch_cn_daily_eastmoney(symbol)
            if df is None or df.empty:
                df = self._fetch_cn_daily_sina(symbol)
            return df

    def _fetch_cn_daily_eastmoney(self, symbol: str) -> Optional[pd.DataFrame]:
        """A 股：东方财富接口"""
        try:
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
            if df is not None and not df.empty:
                return df
        except Exception:
            pass
        return None

    def _fetch_cn_daily_sina(self, symbol: str) -> Optional[pd.DataFrame]:
        """A 股：新浪接口"""
        try:
            sina_symbol = f"sh{symbol}" if symbol.startswith("6") else f"sz{symbol}"
            df = ak.stock_zh_a_daily(symbol=sina_symbol, adjust="qfq")
            if df is not None and not df.empty:
                return df
        except Exception:
            pass
        return None

    def _fetch_us_daily(self, symbol: str) -> Optional[pd.DataFrame]:
        """美股"""
        try:
            df = ak.stock_us_daily(symbol=symbol, adjust="qfq")
            if df is not None and not df.empty:
                return df
        except Exception:
            pass
        return None

    def _normalize_daily(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        标准化日线数据

        自动判断市场类型选择映射
        """
        is_us = bool(symbol.isalpha() or any(c.isalpha() for c in symbol))
        rename_map = self.US_MAP if is_us else self.CN_EASTMONEY_MAP

        df = df.copy()

        # 列名映射
        if rename_map:
            df.rename(columns=rename_map, inplace=True)

        # 统一小写
        df.columns = [c.lower() for c in df.columns]

        return df

    # ==================== 财务数据 ====================

    @classmethod
    def get_cn_financial_data(cls, symbol: str) -> tuple[Optional[dict], dict]:
        """
        使用 AkShare 获取 A 股财务数据（备用方案）

        Args:
            symbol: A 股代码（6位，如 600519）

        Returns:
            (财务数据字典, 原始数据字典)
        """
        financial_data = {}
        raw_data = {}

        try:
            # 使用东方财富个股信息获取基本信息
            df_info = ak.stock_individual_info_em(symbol=symbol)
            if df_info is not None and not df_info.empty:
                raw_data["individual_info"] = df_info.to_dict()

            # 使用财务摘要获取ROE、资产负债率等
            try:
                df_abstract = ak.stock_financial_abstract(symbol=symbol)
                if df_abstract is not None and not df_abstract.empty:
                    raw_data["financial_abstract"] = df_abstract.to_dict()
                    # 从常用指标中提取数据
                    common = cast(pd.DataFrame, df_abstract[df_abstract["选项"] == "常用指标"])
                    if not common.empty:
                        # ROE（净资产收益率）
                        roe_row = cast(pd.DataFrame, common[common["指标"] == "净资产收益率(ROE)"])
                        if len(roe_row) > 0:
                            latest_value = roe_row.iloc[0, 2]
                            if pd.notna(latest_value):
                                financial_data["roe"] = float(latest_value)

                        # 资产负债率
                        debt_row = cast(pd.DataFrame, common[common["指标"] == "资产负债率"])
                        if len(debt_row) > 0:
                            latest_value = debt_row.iloc[0, 2]
                            if pd.notna(latest_value):
                                financial_data["debt_ratio"] = float(latest_value)

                    # 营收增长率
                    growth = cast(pd.DataFrame, df_abstract[df_abstract["选项"] == "成长能力"])
                    if len(growth) > 0:
                        revenue_row = cast(
                            pd.DataFrame,
                            growth[growth["指标"].str.contains("营业收入", na=False)],
                        )
                        if len(revenue_row) > 0:
                            latest_value = revenue_row.iloc[0, 2]
                            if pd.notna(latest_value):
                                financial_data["revenue_growth"] = float(latest_value)

            except Exception as e:
                print(f"⚠️ 获取财务摘要失败: {e}")

        except Exception as e:
            import traceback

            print(f"❌ AkShare获取A股财务数据失败: {e}")
            traceback.print_exc()

        return financial_data if financial_data else None, raw_data
