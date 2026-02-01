"""
股票数据加载器

提供股票日线数据、财务数据获取功能
"""

import re
import akshare as ak
import pandas as pd
import yfinance as yf
from typing import Optional, Tuple

from .stock_list import StockListService
from .sources.tushare import TushareDataSource
from .sources.akshare import AkShareDataSource


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

    US_YFINANCE_MAP = {
        "Date": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
    }

    @staticmethod
    def get_stock_daily(symbol: str) -> Tuple[Optional[pd.DataFrame], str, str]:
        """
        统一入口：获取 [日线数据]、[股票名称] 和 [数据源]
        :param symbol: 股票代码 (如 "600519", "NVDA")
        :return: (DataFrame, stock_name, data_source)
                 如果数据获取失败，DataFrame 为 None, name 为 symbol, data_source 为 ""
        """
        try:
            symbol = str(symbol).strip().upper()
            stock_name = symbol  # 默认名称为代码，防失败
            data_source = ""  # 数据源标识
            df = None

            # --- 1. 判断市场并分发 ---
            if re.search(r"[A-Za-z]", symbol):
                # === 美股处理 ===
                # 1.1 从缓存获取名称
                try:
                    stock_name = DataLoader._get_us_name(symbol)
                except Exception:
                    pass  # 名称获取失败不应阻塞数据获取

                # 1.2 获取数据
                df, data_source = DataLoader._get_us_stock_data(symbol)
            else:
                # === A股处理 ===
                # 1.1 从缓存获取名称
                try:
                    stock_name = DataLoader._get_cn_name(symbol)
                except Exception:
                    pass

                # 1.2 获取数据
                df, data_source = DataLoader._get_cn_stock_data(symbol)

            return df, stock_name, data_source
        except Exception as e:
            print(f"❌ get_stock_daily 异常: {e}")
            # 确保总是返回元组
            try:
                fallback_symbol = str(symbol).strip().upper() if symbol else "UNKNOWN"
            except Exception:
                fallback_symbol = "UNKNOWN"
            return None, fallback_symbol, ""

    # ---------------------------------------------------------
    #  A股 (CN) 专用方法
    # ---------------------------------------------------------
    @staticmethod
    def _get_cn_name(symbol: str) -> str:
        """获取A股名称（从缓存的股票列表读取）"""
        try:
            # 从缓存的股票列表获取名称
            stocks = StockListService.get_a_stock_list()
            for stock in stocks:
                if stock.get("symbol") == symbol:
                    name = stock.get("name")
                    if name:
                        return str(name)
        except Exception as e:
            print(f"⚠️ 从缓存获取A股名称失败: {e}")
        return symbol

    @staticmethod
    def get_stock_info(symbol: str) -> dict:
        """
        获取股票基本信息（名称和行业）

        Args:
            symbol: 股票代码

        Returns:
            包含 name 和 industry 的字典
        """
        symbol = str(symbol).strip().upper()
        info = {"name": symbol, "industry": ""}

        try:
            # 判断市场类型
            is_us = bool(re.search(r"[A-Za-z]", symbol))

            if is_us:
                stocks = StockListService.get_us_stock_list()
            else:
                stocks = StockListService.get_a_stock_list()

            for stock in stocks:
                if stock.get("symbol") == symbol:
                    info["name"] = stock.get("name", symbol)
                    info["industry"] = stock.get("industry", "")
                    break
        except Exception as e:
            print(f"⚠️ 获取股票信息失败: {e}")

        return info

    @staticmethod
    def _get_cn_stock_data(symbol: str) -> Tuple[Optional[pd.DataFrame], str]:
        # 策略 1: Tushare（最高优先级）
        print(f"🇨🇳 [1/3] 正在获取 A股数据: [{symbol}] (Tushare)...")
        df = TushareDataSource.get_daily_data(symbol)
        if df is not None and not df.empty:
            print(f"✓ 使用 Tushare 数据成功 [{symbol}]")
            return DataLoader._standardize_df(df, {}, "CN_Tushare"), "CN_Tushare"

        # 策略 2: 东方财富
        try:
            print(f"🇨🇳 [2/3] 正在获取 A股数据: [{symbol}] (EastMoney)...")
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
            if df is not None and not df.empty:
                return (
                    DataLoader._standardize_df(df, DataLoader.CN_EASTMONEY_MAP, "CN_EastMoney"),
                    "CN_EastMoney",
                )
        except Exception:
            pass

        # 策略 3: 新浪 (备用)
        try:
            print(f"🇨🇳 [3/3] 切换备用源: [{symbol}] (Sina)...")
            sina_symbol = f"sh{symbol}" if symbol.startswith("6") else f"sz{symbol}"
            df = ak.stock_zh_a_daily(symbol=sina_symbol, adjust="qfq")
            if df is not None and not df.empty:
                return DataLoader._standardize_df(df, {}, "CN_Sina"), "CN_Sina"
        except Exception as e:
            print(f"❌ A股数据获取全失败: {e}")

        return None, ""

    # ---------------------------------------------------------
    #  美股 (US) 专用方法
    # ---------------------------------------------------------
    @staticmethod
    def _get_us_name(symbol: str) -> str:
        """获取美股名称（从缓存的股票列表读取）"""
        try:
            # 从缓存的股票列表获取名称
            stocks = StockListService.get_us_stock_list()
            for stock in stocks:
                if stock.get("symbol") == symbol:
                    name = stock.get("name")
                    if name:
                        return str(name)
        except Exception as e:
            print(f"⚠️ 从缓存获取美股名称失败: {e}")
        return symbol

    @staticmethod
    def _get_us_stock_data(symbol: str) -> Tuple[Optional[pd.DataFrame], str]:
        print(f"🇺🇸 正在获取 美股数据: [{symbol}] ...")

        # 策略1: yfinance
        try:
            df = yf.Ticker(symbol).history(period="2y", auto_adjust=False)
            if not df.empty:
                df.reset_index(inplace=True)
                return (
                    DataLoader._standardize_df(df, DataLoader.US_YFINANCE_MAP, "US_yfinance"),
                    "US_yfinance",
                )
        except Exception as e:
            print(f"⚠️ yfinance 失败，尝试 AkShare: {e}")

        # 策略2: AkShare
        try:
            df = ak.stock_us_daily(symbol=symbol, adjust="qfq")
            if df is not None and not df.empty:
                return (
                    DataLoader._standardize_df(df, DataLoader.US_MAP, "US_Sina"),
                    "US_Sina",
                )
        except Exception as e:
            print(f"❌ 美股接口失败: {e}")

        return None, ""

    # ---------------------------------------------------------
    #  通用清洗工具
    # ---------------------------------------------------------
    @staticmethod
    def _standardize_df(df: pd.DataFrame, rename_map: dict, source: str) -> pd.DataFrame:
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

    @staticmethod
    def get_financial_data(symbol: str) -> Tuple[Optional[dict], str]:
        """
        获取股票财务数据（价值投资因子）和数据源

        Args:
            symbol: 股票代码

        Returns:
            (财务数据字典, 数据源标识)
            财务数据字典字段包括：
            - revenue_growth: 营收增长率（%）
            - debt_ratio: 资产负债率（%）
            - pe_ratio: 市盈率
            - pb_ratio: 市净率
            - roe: 净资产收益率（%）
            - raw_data: 原始数据（可选）
        """
        symbol = str(symbol).strip().upper()
        financial_data = {}
        data_source = ""
        raw_data = {}  # 存储原始数据

        # 判断市场类型
        is_us = bool(re.search(r"[A-Za-z]", symbol))

        try:
            if is_us:
                # 美股财务数据（使用 yfinance）
                print(f"📊 正在获取美股财务数据: [{symbol}]...")
                try:
                    info = yf.Ticker(symbol).info
                    if info and isinstance(info, dict):
                        raw_data["info"] = info
                except Exception as e:
                    print(f"⚠️ 获取美股财务数据失败: {e}")
                data_source = "US_yfinance"
                financial_data["raw_data"] = raw_data
            else:
                # A股财务数据
                print(f"📊 正在获取A股财务数据: [{symbol}]...")

                # 优先使用Tushare Pro获取A股财务数据
                financial_data, raw_data = TushareDataSource.get_cn_financial_data(symbol)
                if financial_data:
                    data_source = "CN_Tushare"
                else:
                    # Tushare失败时尝试AkShare
                    print(f"⚠️ Tushare获取失败，尝试AkShare...")
                    financial_data, raw_data = AkShareDataSource.get_cn_financial_data(symbol)
                    if financial_data:
                        data_source = "CN_EastMoney"

                if raw_data and financial_data is not None:
                    financial_data["raw_data"] = raw_data

        except Exception as e:
            print(f"❌ 获取财务数据失败: {e}")

        return financial_data if financial_data else None, data_source
