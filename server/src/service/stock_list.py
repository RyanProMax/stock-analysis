"""
股票列表服务

提供获取A股和美股股票列表的功能
支持 akshare 和 tushare 两种数据源
按日缓存，减少请求频率
"""

import os
from datetime import datetime
from typing import List, Dict, Optional, Any
import pandas as pd
import tushare as ts
from dotenv import load_dotenv


load_dotenv()


class StockListService:
    """股票列表服务类"""

    # Tushare token（从 .env 文件读取）
    TUSHARE_TOKEN = os.environ.get("TUSHARE_TOKEN", "")
    _tushare_pro = None

    # 按日缓存股票列表
    _cache: Dict[str, List[Dict[str, Any]]] = {}
    _cache_date: Optional[str] = None

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
    def _is_cache_valid(cls) -> bool:
        """检查缓存是否有效（当天）"""
        today = cls._get_cache_key()
        return cls._cache_date == today and "A股" in cls._cache

    # 常见美股列表（可以通过其他方式扩展）
    US_STOCKS = [
        # 科技股
        {"code": "AAPL", "name": "Apple Inc.", "market": "美股"},
        {"code": "MSFT", "name": "Microsoft Corporation", "market": "美股"},
        {"code": "GOOGL", "name": "Alphabet Inc.", "market": "美股"},
        {"code": "AMZN", "name": "Amazon.com Inc.", "market": "美股"},
        {"code": "NVDA", "name": "NVIDIA Corporation", "market": "美股"},
        {"code": "META", "name": "Meta Platforms Inc.", "market": "美股"},
        {"code": "TSLA", "name": "Tesla Inc.", "market": "美股"},
        {"code": "NFLX", "name": "Netflix Inc.", "market": "美股"},
        # ETF
        {"code": "TQQQ", "name": "ProShares UltraPro QQQ", "market": "美股"},
        {"code": "TECL", "name": "Direxion Daily Technology Bull 3X", "market": "美股"},
        {"code": "YINN", "name": "Direxion Daily FTSE China Bull 3X", "market": "美股"},
        {"code": "CONL", "name": "GraniteShares 2x Long COIN Daily", "market": "美股"},
        # 中概股
        {"code": "BABA", "name": "Alibaba Group Holding Limited", "market": "美股"},
        {"code": "JD", "name": "JD.com Inc.", "market": "美股"},
        {"code": "PDD", "name": "Pinduoduo Inc.", "market": "美股"},
        {"code": "BIDU", "name": "Baidu Inc.", "market": "美股"},
        {"code": "NIO", "name": "NIO Inc.", "market": "美股"},
        {"code": "XPEV", "name": "XPeng Inc.", "market": "美股"},
        {"code": "LI", "name": "Li Auto Inc.", "market": "美股"},
    ]

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
        # 检查缓存
        if not refresh and cls._is_cache_valid():
            print(f"✓ 使用缓存的A股列表（{cls._cache_date}），共 {len(cls._cache['A股'])} 只股票")
            return cls._cache["A股"]

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

                # 更新缓存
                cls._cache["A股"] = stocks
                cls._cache_date = cls._get_cache_key()
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

            # 更新缓存
            cls._cache["A股"] = stocks
            cls._cache_date = cls._get_cache_key()
            print(f"✓ 使用 AkShare 获取A股列表，共 {len(stocks)} 只股票（已缓存）")
            return stocks
        except Exception as e:
            print(f"⚠️ 获取A股列表失败: {e}")
            return []

        return []

    @classmethod
    def get_us_stock_list(cls) -> List[Dict[str, Any]]:
        """
        获取美股股票列表（转换为tushare格式）

        注意：由于 yfinance 没有直接的列表API，这里返回预设的常见美股列表
        如果需要完整的美股列表，可以考虑使用其他数据源

        Returns:
            List[Dict[str, Any]]: 股票列表，按tushare格式返回
        """
        # 检查缓存
        if cls._is_cache_valid() and "美股" in cls._cache:
            return cls._cache["美股"]

        # 转换为tushare格式
        stocks = []
        for stock in cls.US_STOCKS:
            stocks.append(
                {
                    "ts_code": f"{stock['code']}.US",
                    "symbol": stock["code"],
                    "name": stock["name"],
                    "area": "美国",
                    "industry": None,
                    "market": "美股",
                    "list_date": None,
                }
            )

        # 更新缓存
        cls._cache["美股"] = stocks
        cls._cache_date = cls._get_cache_key()
        return stocks

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
