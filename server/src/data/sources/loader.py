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
from .tushare import TushareDataSource


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
                financial_data, raw_data = DataLoader._get_us_financial_data(symbol)
                data_source = "US_yfinance" if financial_data else ""
                if raw_data and financial_data is not None:
                    financial_data["raw_data"] = raw_data
            else:
                # A股财务数据
                print(f"📊 正在获取A股财务数据: [{symbol}]...")
                data_source = "CN_EastMoney"

                # 使用东方财富实时行情获取PE/PB等估值指标
                try:
                    df_spot = ak.stock_zh_a_spot_em()  # type: ignore
                    if df_spot is not None and not df_spot.empty:
                        stock_row = df_spot[df_spot["代码"] == symbol]
                        if not stock_row.empty:
                            raw_data["spot"] = stock_row.iloc[0].to_dict()
                            # 提取市盈率（动态）
                            pe = stock_row.iloc[0].get("市盈率-动态")
                            if pd.notna(pe) and pe != "-":
                                try:
                                    financial_data["pe_ratio"] = float(pe)
                                except (ValueError, TypeError):
                                    pass
                            # 提取市净率
                            pb = stock_row.iloc[0].get("市净率")
                            if pd.notna(pb) and pb != "-":
                                try:
                                    financial_data["pb_ratio"] = float(pb)
                                except (ValueError, TypeError):
                                    pass
                except Exception as e:
                    print(f"⚠️ 获取估值指标失败: {e}")

                # 尝试从东方财富获取更多财务指标
                try:
                    df_main = ak.stock_financial_analysis_indicator(symbol=symbol)  # type: ignore
                    if df_main is not None and not df_main.empty:
                        raw_data["financial_indicator"] = df_main.iloc[-1].to_dict()
                        latest = df_main.iloc[-1]
                        # 提取营收增长率
                        if "营业收入同比增长率" in df_main.columns:
                            rev_growth = latest.get("营业收入同比增长率", None)
                            if pd.notna(rev_growth):
                                financial_data["revenue_growth"] = float(rev_growth)
                        # 提取资产负债率
                        if "资产负债率" in df_main.columns:
                            debt_ratio = latest.get("资产负债率", None)
                            if pd.notna(debt_ratio):
                                financial_data["debt_ratio"] = float(debt_ratio)
                        # 提取ROE
                        if "净资产收益率" in df_main.columns:
                            roe = latest.get("净资产收益率", None)
                            if pd.notna(roe):
                                financial_data["roe"] = float(roe)
                except Exception as e:
                    print(f"⚠️ 获取财务指标数据失败: {e}")

                # 将原始数据添加到结果中
                if raw_data:
                    financial_data["raw_data"] = raw_data

        except Exception as e:
            print(f"❌ 获取财务数据失败: {e}")

        return financial_data if financial_data else None, data_source

    @staticmethod
    def _get_us_financial_data(symbol: str) -> Tuple[Optional[dict], dict]:
        """
        使用 yfinance 获取美股财务数据

        Args:
            symbol: 美股代码

        Returns:
            (财务数据字典, 原始数据字典)
        """
        financial_data = {}
        raw_data = {}  # 存储原始数据

        try:
            # 创建股票对象
            ticker = yf.Ticker(symbol)

            # 获取基本信息（包含PE、PB等估值指标）
            try:
                info = ticker.info

                # 保存原始info数据（选择性保存关键字段）
                if info is not None and isinstance(info, dict) and len(info) > 0:
                    raw_data["info"] = {
                        k: v
                        for k, v in info.items()
                        if k
                        in [
                            "trailingPE",
                            "forwardPE",
                            "priceToBook",
                            "returnOnEquity",
                            "profitMargins",
                            "revenueGrowth",
                            "marketCap",
                            "debtToEquity",
                            "currentRatio",
                            "quickRatio",
                            "operatingMargins",
                            "grossMargins",
                        ]
                    }

                    # 提取市盈率
                    if "trailingPE" in info and info["trailingPE"] is not None:
                        financial_data["pe_ratio"] = float(info["trailingPE"])
                    elif "forwardPE" in info and info["forwardPE"] is not None:
                        financial_data["pe_ratio"] = float(info["forwardPE"])

                    # 提取市净率
                    if "priceToBook" in info and info["priceToBook"] is not None:
                        financial_data["pb_ratio"] = float(info["priceToBook"])

                    # 提取ROE（净资产收益率）
                    if "returnOnEquity" in info and info["returnOnEquity"] is not None:
                        # yfinance返回的是小数形式（如0.15表示15%），需要转换为百分比
                        financial_data["roe"] = float(info["returnOnEquity"]) * 100

                    # 提取营收增长率（如果info中有）
                    if "revenueGrowth" in info and info["revenueGrowth"] is not None:
                        financial_data["revenue_growth"] = float(info["revenueGrowth"]) * 100
                else:
                    print(f"⚠️ ticker.info 为空或无效")

            except Exception as e:
                print(f"⚠️ 获取基本信息失败: {e}")

            # 获取财务报表数据
            try:
                # 获取利润表（用于计算营收增长率）
                financials = ticker.financials
                if financials is not None and hasattr(financials, "empty") and not financials.empty:
                    # 查找总营收（Total Revenue）
                    # yfinance的financials是DataFrame，行索引是指标名称，列是日期
                    revenue_rows = [
                        idx
                        for idx in financials.index
                        if "revenue" in str(idx).lower() and "total" in str(idx).lower()
                    ]

                    if not revenue_rows:
                        # 如果没有找到Total Revenue，尝试找其他营收相关指标
                        revenue_rows = [
                            idx for idx in financials.index if "revenue" in str(idx).lower()
                        ]

                    if revenue_rows:
                        revenue_row = revenue_rows[0]
                        try:
                            # 获取最近两年的营收数据（列是日期，最新的在最前面）
                            revenue_data = financials.loc[revenue_row].dropna()
                            if len(revenue_data) >= 2:
                                # 计算营收增长率（最新一年 vs 前一年）
                                latest_revenue = float(revenue_data.iloc[0])
                                prev_revenue = float(revenue_data.iloc[1])
                                if prev_revenue != 0:
                                    revenue_growth = (
                                        (latest_revenue - prev_revenue) / abs(prev_revenue)
                                    ) * 100
                                    financial_data["revenue_growth"] = revenue_growth
                        except (IndexError, KeyError, ValueError) as e:
                            print(f"⚠️ 计算营收增长率失败: {e}")

                # 获取资产负债表（用于计算资产负债率）
                balance_sheet = ticker.balance_sheet
                if (
                    balance_sheet is not None
                    and hasattr(balance_sheet, "empty")
                    and not balance_sheet.empty
                ):
                    # 查找总资产和总负债（行索引是指标名称）
                    total_assets_rows = [
                        idx
                        for idx in balance_sheet.index
                        if "total assets" in str(idx).lower() or "totalassets" in str(idx).lower()
                    ]
                    total_liab_rows = [
                        idx
                        for idx in balance_sheet.index
                        if (
                            "total liabilities" in str(idx).lower()
                            or "totalliab" in str(idx).lower()
                        )
                        and "non" not in str(idx).lower()  # 排除非流动负债
                    ]

                    if total_assets_rows and total_liab_rows:
                        try:
                            assets_series = balance_sheet.loc[total_assets_rows[0]]
                            liab_series = balance_sheet.loc[total_liab_rows[0]]

                            if not assets_series.empty and not liab_series.empty:
                                total_assets = float(assets_series.iloc[0])
                                total_liab = float(liab_series.iloc[0])

                                if (
                                    pd.notna(total_assets)
                                    and pd.notna(total_liab)
                                    and total_assets != 0
                                ):
                                    debt_ratio = (total_liab / total_assets) * 100
                                    financial_data["debt_ratio"] = debt_ratio
                        except (IndexError, KeyError, ValueError) as e:
                            print(f"⚠️ 计算资产负债率失败: {e}")

            except Exception as e:
                print(f"⚠️ 获取财务报表数据失败: {e}")

            # 如果ROE未从info获取，尝试从财务报表计算
            if "roe" not in financial_data:
                try:
                    # ROE = 净利润 / 股东权益
                    financials = ticker.financials
                    balance_sheet = ticker.balance_sheet

                    if (
                        financials is not None
                        and hasattr(financials, "empty")
                        and not financials.empty
                        and balance_sheet is not None
                        and hasattr(balance_sheet, "empty")
                        and not balance_sheet.empty
                    ):
                        # 查找净利润（行索引是指标名称）
                        net_income_rows = [
                            idx
                            for idx in financials.index
                            if "net income" in str(idx).lower() or "netincome" in str(idx).lower()
                        ]
                        # 查找股东权益
                        equity_rows = [
                            idx
                            for idx in balance_sheet.index
                            if (
                                "total stockholders equity" in str(idx).lower()
                                or "totalstockholderequity" in str(idx).lower()
                                or "stockholders equity" in str(idx).lower()
                            )
                            and "non" not in str(idx).lower()
                        ]

                        if net_income_rows and equity_rows:
                            try:
                                net_income_series = financials.loc[net_income_rows[0]]
                                equity_series = balance_sheet.loc[equity_rows[0]]

                                if not net_income_series.empty and not equity_series.empty:
                                    net_income = float(net_income_series.iloc[0])
                                    equity = float(equity_series.iloc[0])

                                    if pd.notna(net_income) and pd.notna(equity) and equity != 0:
                                        roe = (net_income / equity) * 100
                                        financial_data["roe"] = roe
                            except (IndexError, KeyError, ValueError) as e:
                                print(f"⚠️ 计算ROE失败: {e}")
                except Exception as e:
                    print(f"⚠️ 计算ROE失败: {e}")

        except Exception as e:
            import traceback

            print(f"❌ 获取美股财务数据失败: {e}")
            print("美股财务数据获取错误堆栈:")
            traceback.print_exc()

        return financial_data if financial_data else None, raw_data
