"""
股票列表服务

提供获取A股和美股股票列表的功能
- A股：支持 tushare 和 akshare 两种数据源
- 美股：支持 tushare 和 NASDAQ API 两种数据源
按日缓存，减少请求频率
"""

import os
from datetime import datetime
from typing import List, Dict, Optional, Any
import pandas as pd
import akshare as ak
import tushare as ts
import requests
from dotenv import load_dotenv
from ..cache_util import CacheUtil

load_dotenv()


class StockListService:
    """股票列表服务类"""

    # Tushare token（从 .env 文件读取）
    TUSHARE_TOKEN = os.environ.get("TUSHARE_TOKEN", "")
    _tushare_pro = None

    # 按日缓存股票列表
    # 缓存结构：{市场类型: 股票列表}
    _cache: Dict[str, List[Dict[str, Any]]] = {}
    # 每个市场类型的缓存日期：{市场类型: 日期字符串}
    _cache_date: Dict[str, str] = {}

    @classmethod
    def _get_tushare_pro(cls):
        """获取 tushare pro 实例（懒加载）"""
        if cls._tushare_pro is not None:
            return cls._tushare_pro

        if not cls.TUSHARE_TOKEN:
            print("⚠️ Tushare token 未配置，将使用 akshare 作为数据源")
            return None

        try:
            if ts is not None:
                ts.set_token(cls.TUSHARE_TOKEN)
                cls._tushare_pro = ts.pro_api()
                print("✓ Tushare 初始化成功")
                return cls._tushare_pro
            return None
        except Exception as e:
            print(f"⚠️ Tushare 初始化失败: {e}")
            return None

    @classmethod
    def _get_cache_key(cls) -> str:
        """获取缓存键（按日期）"""
        return datetime.now().strftime("%Y-%m-%d")

    @classmethod
    def _is_cache_valid(cls, market: str) -> bool:
        """
        检查指定市场类型的缓存是否有效（当天且列表不为空）

        Args:
            market: 市场类型（"A股" 或 "美股"）

        Returns:
            bool: 缓存是否有效（缓存存在、日期为今天、且列表不为空）
        """
        today = cls._get_cache_key()
        return (
            market in cls._cache
            and market in cls._cache_date
            and cls._cache_date[market] == today
            and len(cls._cache[market]) > 0  # 缓存列表不能为空
        )

    @classmethod
    def get_a_stock_list(
        cls, use_tushare: bool = True, refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        获取A股股票列表（按tushare格式原样返回）

        Args:
            use_tushare: 是否优先使用 tushare（更准确），如果不可用则回退到 akshare
            refresh: 是否强制刷新缓存

        Returns:
            List[Dict[str, Any]]: 股票列表，按tushare格式返回（ts_code, symbol, name, area, industry, market, list_date等）
        """
        # 检查内存缓存（如果缓存为空，也会重新获取）
        market = "A股"
        if not refresh and cls._is_cache_valid(market):
            print(
                f"✓ 使用内存缓存的A股列表（{cls._cache_date[market]}），共 {len(cls._cache[market])} 只股票"
            )
            return cls._cache[market]

        # 检查文件缓存
        if not refresh:
            cached_data = CacheUtil.load_stock_list(market)
            if cached_data is not None:
                # 更新内存缓存
                cls._cache[market] = cached_data
                cls._cache_date[market] = cls._get_cache_key()
                print(f"✓ 使用文件缓存的A股列表，共 {len(cached_data)} 只股票")
                return cached_data

        # 优先使用 tushare（如果可用且配置了 token）
        tushare_pro = cls._get_tushare_pro()
        if use_tushare and tushare_pro is not None:
            try:
                # 使用 tushare 获取A股列表，获取所有字段
                df = tushare_pro.stock_basic(exchange="", list_status="L")
                # 将 DataFrame 转换为字典列表（原样返回tushare格式）
                stocks = df.to_dict("records")
                # 确保所有值都是字符串或可序列化类型
                for stock in stocks:
                    for key, value in stock.items():
                        if pd.isna(value):
                            stock[key] = None
                        else:
                            stock[key] = (
                                str(value) if not isinstance(value, (int, float, bool)) else value
                            )

                # 更新缓存（内存 + 文件）
                market = "A股"
                cls._cache[market] = stocks
                cls._cache_date[market] = cls._get_cache_key()
                CacheUtil.save_stock_list(market, stocks)
                print(f"✓ 使用 Tushare 获取A股列表，共 {len(stocks)} 只股票（已缓存）")
                return stocks
            except Exception as e:
                print(f"⚠️ Tushare 获取A股列表失败，回退到 akshare: {e}")

        # 回退到 akshare（转换为tushare格式）
        try:
            df = ak.stock_info_a_code_name()
            stocks = []
            for _, row in df.iterrows():
                # 转换为tushare格式
                symbol = str(row["code"]).strip()
                name = str(row["name"]).strip()
                # 根据代码判断交易所
                if symbol.startswith("6"):
                    ts_code = f"{symbol}.SH"
                    market = "主板"
                elif symbol.startswith(("0", "3")):
                    ts_code = f"{symbol}.SZ"
                    market = "主板" if symbol.startswith("0") else "创业板"
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

            # 更新缓存（内存 + 文件）
            market = "A股"
            cls._cache[market] = stocks
            cls._cache_date[market] = cls._get_cache_key()
            CacheUtil.save_stock_list(market, stocks)
            print(f"✓ 使用 AkShare 获取A股列表，共 {len(stocks)} 只股票（已缓存）")
            return stocks
        except Exception as e:
            print(f"⚠️ 获取A股列表失败: {e}")
            # 如果获取失败，清除缓存，下次重新尝试
            if market in cls._cache:
                del cls._cache[market]
            if market in cls._cache_date:
                del cls._cache_date[market]
            return []

        return []

    @classmethod
    def get_us_stock_list(
        cls, use_tushare: bool = True, refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        获取美股股票列表（按tushare格式原样返回）

        Args:
            use_tushare: 是否允许使用 tushare 作为兜底（优先使用 NASDAQ API）
            refresh: 是否强制刷新缓存

        Returns:
            List[Dict[str, Any]]: 股票列表，按tushare格式返回（ts_code, symbol, name, area, industry, market, list_date等）
        """
        # 检查内存缓存（如果缓存为空，也会重新获取）
        market = "美股"
        if not refresh and cls._is_cache_valid(market):
            print(
                f"✓ 使用内存缓存的美股列表（{cls._cache_date[market]}），共 {len(cls._cache[market])} 只股票"
            )
            return cls._cache[market]

        # 检查文件缓存
        if not refresh:
            cached_data = CacheUtil.load_stock_list(market)
            if cached_data is not None:
                # 更新内存缓存
                cls._cache[market] = cached_data
                cls._cache_date[market] = cls._get_cache_key()
                print(f"✓ 使用文件缓存的美股列表，共 {len(cached_data)} 只股票")
                return cached_data

        # 优先使用 NASDAQ API
        print("⚠️ 尝试使用 NASDAQ API 获取美股列表...")
        try:
            # 请求 NASDAQ API
            url = "https://api.nasdaq.com/api/screener/stocks"
            params = {"tableonly": "true", "limit": "5000", "download": "true"}
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()

            # 解析 NASDAQ API 返回的数据结构
            # 根据实际 API 响应格式调整
            stocks = []
            if "data" in data and "rows" in data["data"]:
                rows = data["data"]["rows"]
                for row in rows:
                    # 根据实际 API 返回的字段名调整
                    symbol = str(row.get("symbol") or row.get("ticker") or "").strip()
                    name = str(row.get("name") or row.get("companyName") or "").strip()
                    industry = str(row.get("sector") or row.get("industry") or "").strip()

                    if not symbol or not name or symbol == "nan" or name == "nan":
                        continue

                    # 转换为tushare格式
                    stocks.append(
                        {
                            "ts_code": f"{symbol}.US",  # 美股使用 .US 后缀
                            "symbol": symbol,
                            "name": name,
                            "area": "美国",
                            "industry": (industry if industry and industry != "nan" else None),
                            "market": "美股",
                            "list_date": None,
                        }
                    )
            elif "data" in data and isinstance(data["data"], list):
                # 如果返回的是列表格式
                for row in data["data"]:
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
                            "industry": (industry if industry and industry != "nan" else None),
                            "market": "美股",
                            "list_date": None,
                        }
                    )

            # 只有当获取到数据时才更新缓存（避免缓存空列表）
            if len(stocks) > 0:
                cls._cache[market] = stocks
                cls._cache_date[market] = cls._get_cache_key()
                CacheUtil.save_stock_list(market, stocks)
                print(f"✓ 使用 NASDAQ API 获取美股列表，共 {len(stocks)} 只股票（已缓存）")
                return stocks
            else:
                # 如果获取失败或列表为空，清除缓存，下次重新尝试
                if market in cls._cache:
                    del cls._cache[market]
                if market in cls._cache_date:
                    del cls._cache_date[market]
                print("⚠️ NASDAQ API 返回数据为空，尝试回退到 Tushare...")
        except Exception as e:
            print(f"⚠️ NASDAQ API 获取美股列表失败，回退到 Tushare: {type(e).__name__}: {e}")

        # 回退到 tushare（如果可用且配置了 token）
        if use_tushare:
            tushare_pro = cls._get_tushare_pro()
            if tushare_pro is not None:
                try:
                    # 使用 tushare 获取美股列表，获取所有字段
                    df = tushare_pro.us_basic()
                    # 将 DataFrame 转换为字典列表（原样返回tushare格式）
                    stocks = df.to_dict("records")
                    # 确保所有值都是字符串或可序列化类型
                    for stock in stocks:
                        for key, value in stock.items():
                            if pd.isna(value):
                                stock[key] = None
                            else:
                                stock[key] = (
                                    str(value)
                                    if not isinstance(value, (int, float, bool))
                                    else value
                                )

                    # 更新缓存（内存 + 文件）
                    cls._cache[market] = stocks
                    cls._cache_date[market] = cls._get_cache_key()
                    CacheUtil.save_stock_list(market, stocks)
                    print(f"✓ 使用 Tushare 获取美股列表，共 {len(stocks)} 只股票（已缓存）")
                    return stocks
                except Exception as e:
                    print(f"⚠️ Tushare 获取美股列表也失败: {type(e).__name__}: {e}")

        # 如果所有数据源都失败，清除缓存，下次重新尝试
        if market in cls._cache:
            del cls._cache[market]
        if market in cls._cache_date:
            del cls._cache_date[market]
        print("⚠️ 所有数据源都失败，无法获取美股列表")
        return []

    @classmethod
    def get_all_stock_list(cls) -> List[Dict[str, Any]]:
        """
        获取所有股票列表（A股 + 美股）

        Returns:
            List[Dict[str, Any]]: 股票列表，按tushare格式返回
        """
        a_stocks = cls.get_a_stock_list()
        us_stocks = cls.get_us_stock_list()
        return a_stocks + us_stocks

    @classmethod
    def search_stocks(cls, keyword: str, market: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        搜索股票（从缓存列表中搜索）

        Args:
            keyword: 搜索关键词（可以是代码或名称）
            market: 市场类型（"A股" 或 "美股"），如果为 None 则搜索所有市场

        Returns:
            List[Dict[str, Any]]: 匹配的股票列表，按tushare格式返回
        """
        keyword = keyword.upper().strip()
        if not keyword:
            return []

        # 从缓存中获取股票列表
        if market == "A股":
            all_stocks = cls.get_a_stock_list()
        elif market == "美股":
            all_stocks = cls.get_us_stock_list()
        else:
            all_stocks = cls.get_all_stock_list()

        # 搜索匹配（在 ts_code, symbol, name 中搜索）
        results = []
        for stock in all_stocks:
            ts_code = str(stock.get("ts_code", "")).upper()
            symbol = str(stock.get("symbol", "")).upper()
            name = str(stock.get("name", "")).upper()
            if keyword in ts_code or keyword in symbol or keyword in name:
                results.append(stock)

        return results
