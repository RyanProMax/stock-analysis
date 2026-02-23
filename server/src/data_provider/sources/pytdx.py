"""
Pytdx 数据源

使用 pytdx（通达信）获取 A 股日线数据、实时行情

特点：
- 直连通达信行情服务器
- 多服务器自动切换
- 支持实时行情
- 无需 Token
"""

from typing import List, Dict, Any, Optional, Tuple, Generator
from contextlib import contextmanager
import pandas as pd
from pytdx.hq import TdxHq_API
import re
import logging
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from ..base import BaseStockDataSource
from ..realtime_types import UnifiedRealtimeQuote, RealtimeSource


logger = logging.getLogger(__name__)

# 默认通达信行情服务器列表
DEFAULT_HOSTS: List[Tuple[str, int]] = [
    ("119.147.212.81", 7709),  # 深圳
    ("112.74.214.43", 7727),  # 深圳
    ("221.231.141.60", 7709),  # 上海
    ("101.227.73.20", 7709),  # 上海
    ("101.227.77.254", 7709),  # 上海
    ("14.215.128.18", 7709),  # 广州
    ("59.173.18.140", 7709),  # 武汉
    ("180.153.39.51", 7709),  # 杭州
]


class PytdxDataSource(BaseStockDataSource):
    """Pytdx 数据源（通达信）"""

    SOURCE_NAME: str = "Pytdx"
    priority: int = 2  # A股优先级 2

    def __init__(self):
        super().__init__()
        self._hosts = self._parse_hosts_from_env() or DEFAULT_HOSTS
        self._current_host_idx = 0
        self._stock_name_cache: Dict[str, str] = {}
        self._stock_list_cache: Optional[List[Dict]] = None

    # ==================== 股票列表 ====================

    def fetch_a_stocks(self) -> List[Dict[str, Any]]:
        """获取 A 股股票列表"""
        try:
            api_class = self._get_pytdx()
            if api_class is None:
                return []

            with self._pytdx_session() as api:
                stocks = []

                # 获取深圳股票列表
                sz_stocks = api.get_security_list(0, 0)  # 深圳
                for stock in sz_stocks or []:
                    code = stock["code"]
                    stocks.append(
                        {
                            "ts_code": f"{code}.SZ",
                            "symbol": code,
                            "name": stock.get("name", ""),
                            "area": None,
                            "industry": None,
                            "market": self._get_market_type(code),
                            "list_date": None,
                        }
                    )

                # 获取上海股票列表
                sh_stocks = api.get_security_list(1, 0)  # 上海
                for stock in sh_stocks or []:
                    code = stock["code"]
                    stocks.append(
                        {
                            "ts_code": f"{code}.SH",
                            "symbol": code,
                            "name": stock.get("name", ""),
                            "area": None,
                            "industry": None,
                            "market": self._get_market_type(code),
                            "list_date": None,
                        }
                    )

                return stocks

        except Exception as e:
            logger.warning(f"获取A股列表失败: {e}")
            return []

    def fetch_us_stocks(self) -> List[Dict[str, Any]]:
        """Pytdx 不支持美股列表"""
        return []

    # ==================== 日线数据 ====================

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def _fetch_raw_daily(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        获取原始日线数据

        Args:
            symbol: 股票代码

        Returns:
            原始 DataFrame，失败返回 None
        """
        # 美股不支持
        if self._is_us_code(symbol):
            logger.warning(f"Pytdx 不支持美股 {symbol}")
            return None

        api_class = self._get_pytdx()
        if api_class is None:
            return None

        try:
            market, code = self._get_market_code(symbol)

            with self._pytdx_session() as api:
                # 计算需要获取的交易日数量（估算）
                from datetime import datetime as dt, timedelta

                end_date = dt.now()
                start_date = end_date - timedelta(days=730)
                days = (end_date - start_date).days
                count = min(max(days * 5 // 7 + 10, 30), 800)  # 最大 800 条

                # 获取日 K 线数据
                data = api.get_security_bars(
                    category=9,  # 日线
                    market=market,
                    code=code,
                    start=0,  # 从最新开始
                    count=count,
                )

                # 转换为 DataFrame
                df = api.to_df(data)

                # 过滤日期范围
                df["datetime"] = pd.to_datetime(df["datetime"])
                df = df[(df["datetime"] >= start_date) & (df["datetime"] <= end_date)]

                return df

        except Exception as e:
            logger.warning(f"获取股票 {symbol} 数据失败: {e}")
            return None

    def _normalize_daily(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        标准化日线数据

        Args:
            df: 原始 DataFrame
            symbol: 股票代码

        Returns:
            标准化后的 DataFrame
        """
        df = df.copy()

        # 列名映射
        column_mapping = {"datetime": "date", "vol": "volume"}
        df.rename(columns=column_mapping, inplace=True)

        # 计算涨跌幅（pytdx 不返回涨跌幅）
        if "pct_chg" not in df.columns and "close" in df.columns:
            df["pct_chg"] = df["close"].pct_change() * 100
            df["pct_chg"] = df["pct_chg"].fillna(0).round(2)

        # 添加股票代码列
        df["code"] = symbol

        # 只保留需要的列
        keep_cols = ["code"] + self.STANDARD_DAILY_COLUMNS
        existing_cols = [col for col in keep_cols if col in df.columns]
        df = df[existing_cols]

        return df

    # ==================== 实时行情 ====================

    def get_realtime_quote(self, symbol: str) -> Optional[UnifiedRealtimeQuote]:
        """
        获取实时行情

        Args:
            symbol: 股票代码

        Returns:
            UnifiedRealtimeQuote 对象，失败返回 None
        """
        # 美股不支持
        if self._is_us_code(symbol):
            return None

        api_class = self._get_pytdx()
        if api_class is None:
            return None

        try:
            market, code = self._get_market_code(symbol)

            with self._pytdx_session() as api:
                data = api.get_security_quotes([(market, code)])

                if data and len(data) > 0:
                    quote = data[0]

                    # 计算涨跌幅
                    price = self._safe_float(quote.get("price"))
                    pre_close = self._safe_float(quote.get("last_close"))
                    change_pct = None
                    change_amount = None
                    if price is not None and pre_close is not None and pre_close > 0:
                        change_amount = price - pre_close
                        change_pct = (change_amount / pre_close) * 100

                    return UnifiedRealtimeQuote(
                        code=symbol,
                        name=quote.get("name", ""),
                        source=RealtimeSource.PYTDX,
                        price=price,
                        change_pct=change_pct,
                        change_amount=change_amount,
                        open_price=self._safe_float(quote.get("open")),
                        high=self._safe_float(quote.get("high")),
                        low=self._safe_float(quote.get("low")),
                        pre_close=pre_close,
                        volume=self._safe_int(quote.get("vol")),
                        amount=self._safe_float(quote.get("amount")),
                    )

        except Exception as e:
            logger.warning(f"获取 {symbol} 实时行情失败: {e}")

        return None

    # ==================== 可用性检查 ====================

    def is_available(self, market: str) -> bool:
        """
        检查数据源是否可用于指定市场

        Args:
            market: 市场类型（"A股" 或 "美股"）

        Returns:
            是否可用
        """
        return market == "A股"

    # ==================== 上下文管理器 ====================

    @contextmanager
    def _pytdx_session(self) -> Generator:
        """
        Pytdx 连接上下文管理器

        确保：
        1. 进入上下文时自动连接
        2. 退出上下文时自动断开
        3. 异常时也能正确断开
        """
        api_class = self._get_pytdx()
        if api_class is None:
            raise ImportError("pytdx 库未安装")

        api = api_class()
        connected = False

        try:
            # 尝试连接服务器（自动选择最优）
            for i in range(len(self._hosts)):
                host_idx = (self._current_host_idx + i) % len(self._hosts)
                host, port = self._hosts[host_idx]

                try:
                    if api.connect(host, port, time_out=5):
                        connected = True
                        self._current_host_idx = host_idx
                        logger.debug(f"Pytdx 连接成功: {host}:{port}")
                        break
                except Exception as e:
                    logger.debug(f"Pytdx 连接 {host}:{port} 失败: {e}")
                    continue

            if not connected:
                raise ConnectionError("Pytdx 无法连接任何服务器")

            yield api

        finally:
            # 确保断开连接
            try:
                api.disconnect()
                logger.debug("Pytdx 连接已断开")
            except Exception as e:
                logger.warning(f"Pytdx 断开连接时出错: {e}")

    # ==================== 工具方法 ====================

    @staticmethod
    def _get_pytdx():
        """获取 pytdx 模块"""
        return TdxHq_API

    def _get_market_code(self, stock_code: str) -> Tuple[int, str]:
        """
        根据股票代码判断市场

        Pytdx 市场代码：
        - 0: 深圳
        - 1: 上海
        """
        code = stock_code.strip()

        # 去除可能的前缀后缀
        code = code.replace(".SH", "").replace(".SZ", "").replace(".sh", "").replace(".sz", "")
        code = code.replace("sh", "").replace("sz", "")

        # 根据代码前缀判断市场
        if code.startswith(("60", "68")):
            return 1, code  # 上海
        else:
            return 0, code  # 深圳

    @staticmethod
    def _is_us_code(stock_code: str) -> bool:
        """判断代码是否为美股"""
        code = stock_code.strip().upper()
        return bool(re.match(r"^[A-Z]{1,5}(\.[A-Z])?$", code))

    @staticmethod
    def _get_market_type(code: str) -> str:
        """根据代码判断市场类型"""
        if code.startswith("6"):
            return "主板"
        elif code.startswith("0"):
            return "主板"
        elif code.startswith("3"):
            return "创业板"
        elif code.startswith("68"):
            return "科创板"
        else:
            return "其他"

    @staticmethod
    def _parse_hosts_from_env() -> Optional[List[Tuple[str, int]]]:
        """从环境变量解析服务器配置"""
        import os

        # 优先级：PYTDX_SERVERS > PYTDX_HOST + PYTDX_PORT
        servers_str = os.getenv("PYTDX_SERVERS", "")
        if servers_str:
            try:
                hosts = []
                for s in servers_str.split(","):
                    parts = s.strip().split(":")
                    if len(parts) == 2:
                        hosts.append((parts[0], int(parts[1])))
                if hosts:
                    return hosts
            except Exception:
                pass

        host = os.getenv("PYTDX_HOST", "")
        port = os.getenv("PYTDX_PORT", "")
        if host and port:
            try:
                return [(host, int(port))]
            except Exception:
                pass

        return None

    @staticmethod
    def _safe_float(value) -> Optional[float]:
        """安全转换为 float"""
        try:
            if pd.isna(value) or value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_int(value) -> Optional[int]:
        """安全转换为 int"""
        try:
            if pd.isna(value) or value is None:
                return None
            return int(float(value))
        except (TypeError, ValueError):
            return None
