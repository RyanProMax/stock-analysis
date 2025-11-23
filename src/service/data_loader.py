import re
import akshare as ak
import pandas as pd
from typing import Optional, Tuple


class DataLoader:
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

    @staticmethod
    def get_stock_daily(symbol: str) -> Tuple[Optional[pd.DataFrame], str]:
        """
        统一入口：获取 [日线数据] 和 [股票名称]
        :param symbol: 股票代码 (如 "600519", "NVDA")
        :return: (DataFrame, stock_name)
                 如果数据获取失败，DataFrame 为 None, name 为 symbol
        """
        symbol = str(symbol).strip().upper()
        stock_name = symbol  # 默认名称为代码，防失败
        df = None

        # --- 1. 判断市场并分发 ---
        if re.search(r"[A-Za-z]", symbol):
            # === 美股处理 ===
            # 1.1 获取名称
            try:
                stock_name = DataLoader._get_us_name(symbol)
            except Exception:
                pass  # 名称获取失败不应阻塞数据获取

            # 1.2 获取数据
            df = DataLoader._get_us_stock_data(symbol)
        else:
            # === A股处理 ===
            # 1.1 获取名称
            try:
                stock_name = DataLoader._get_cn_name(symbol)
            except Exception:
                pass

            # 1.2 获取数据
            df = DataLoader._get_cn_stock_data(symbol)

        return df, stock_name

    # ---------------------------------------------------------
    #  A股 (CN) 专用方法
    # ---------------------------------------------------------
    @staticmethod
    def _get_cn_name(symbol: str) -> str:
        """获取A股名称 (使用东方财富个股信息接口)"""
        try:
            # 返回包含 '股票代码', '股票简称' 等信息的 DataFrame
            df_info = ak.stock_individual_info_em(symbol=symbol)
            # 筛选出 '股票简称' 对应的值
            name_row = df_info[df_info["item"] == "股票简称"]
            if not name_row.empty:
                return name_row["value"].values[0]
        except Exception as e:
            print(f"⚠️ 获取A股名称失败: {e}")
        return symbol

    @staticmethod
    def _get_cn_stock_data(symbol: str) -> Optional[pd.DataFrame]:
        # 策略 1: 东方财富
        try:
            print(f"🇨🇳 [1/2] 正在获取 A股数据: [{symbol}] (EastMoney)...")
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
            if not df.empty:
                return DataLoader._standardize_df(
                    df, DataLoader.CN_EASTMONEY_MAP, "CN_EastMoney"
                )
        except Exception:
            pass

        # 策略 2: 新浪 (备用)
        try:
            print(f"🇨🇳 [2/2] 切换备用源: [{symbol}] (Sina)...")
            sina_symbol = f"sh{symbol}" if symbol.startswith("6") else f"sz{symbol}"
            df = ak.stock_zh_a_daily(symbol=sina_symbol, adjust="qfq")
            if not df.empty:
                return DataLoader._standardize_df(df, {}, "CN_Sina")
        except Exception as e:
            print(f"❌ A股数据获取全失败: {e}")

        return None

    # ---------------------------------------------------------
    #  美股 (US) 专用方法
    # ---------------------------------------------------------
    @staticmethod
    def _get_us_name(symbol: str) -> str:
        """获取美股名称"""
        return symbol

    @staticmethod
    def _get_us_stock_data(symbol: str) -> Optional[pd.DataFrame]:
        print(f"🇺🇸 正在获取 美股数据: [{symbol}] ...")
        try:
            df = ak.stock_us_daily(symbol=symbol, adjust="qfq")
            if not df.empty:
                return DataLoader._standardize_df(df, DataLoader.US_MAP, "US_Sina")
        except Exception as e:
            print(f"❌ 美股接口失败: {e}")
        return None

    # ---------------------------------------------------------
    #  通用清洗工具
    # ---------------------------------------------------------
    @staticmethod
    def _standardize_df(
        df: pd.DataFrame, rename_map: dict, source: str
    ) -> pd.DataFrame:
        if rename_map:
            df.rename(columns=rename_map, inplace=True)
        df.columns = [c.lower() for c in df.columns]

        # 处理日期
        date_col = next((c for c in ["date", "日期"] if c in df.columns), None)
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col])
            df.set_index(date_col, inplace=True)
            df.index.name = "date"
            df.sort_index(inplace=True)

        # 强转数值
        for col in ["open", "close", "high", "low", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        return df
