"""
Baostock 数据源

使用 Baostock 获取 A 股日线数据

特点：
- 免费，需登录
- 数据有延迟（T+1）
- 不支持实时行情
- 不支持美股
"""

from typing import List, Dict, Any, Optional, Generator
from contextlib import contextmanager
import pandas as pd
import baostock as bs
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
from ..realtime_types import UnifiedRealtimeQuote


logger = logging.getLogger(__name__)


class BaostockDataSource(BaseStockDataSource):
    """Baostock 数据源"""

    SOURCE_NAME: str = "Baostock"
    priority: int = 3  # A股优先级 3（最低）

    def __init__(self):
        super().__init__()
        self._stock_name_cache: Dict[str, str] = {}

    # ==================== 股票列表 ====================

    def fetch_a_stocks(self) -> List[Dict[str, Any]]:
        """获取 A 股股票列表"""
        try:
            bs_class = self._get_baostock()
            if bs_class is None:
                return []

            with self._baostock_session() as bs:
                stocks = []

                # 获取股票列表
                rs = bs.query_stock_basic()
                if rs is None or rs.error_code != "0":
                    logger.warning(f"获取股票列表失败: {rs.error_msg}")
                    return []

                while rs.next():
                    row = rs.get_row_data()
                    code = row[0]  # 证券代码
                    name = row[2]  # 证券名称

                    # 缓存股票名称
                    self._stock_name_cache[code] = name

                    # 解析市场类型
                    market_type = self._parse_market_type(code)

                    # 去掉市场前缀
                    symbol = code.replace("sh.", "").replace("sz.", "")
                    ts_code = f"{symbol}.SH" if code.startswith("sh.") else f"{symbol}.SZ"

                    stocks.append(
                        {
                            "ts_code": ts_code,
                            "symbol": symbol,
                            "name": name,
                            "area": None,
                            "industry": None,
                            "market": market_type,
                            "list_date": None,
                        }
                    )

                return stocks

        except Exception as e:
            logger.warning(f"获取A股列表失败: {e}")
            return []

    def fetch_us_stocks(self) -> List[Dict[str, Any]]:
        """Baostock 不支持美股列表"""
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
            logger.warning(f"Baostock 不支持美股 {symbol}")
            return None

        bs_class = self._get_baostock()
        if bs_class is None:
            return None

        try:
            # 转换代码格式
            bs_code = self._convert_stock_code(symbol)

            with self._baostock_session() as bs:
                # 计算日期范围（最近2年）
                from datetime import datetime, timedelta

                end_date = datetime.now().strftime("%Y-%m-%d")
                start_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")

                # 查询日线数据
                rs = bs.query_history_k_data_plus(
                    code=bs_code,
                    fields="date,open,high,low,close,volume,amount,pctChg",
                    start_date=start_date,
                    end_date=end_date,
                    frequency="d",  # 日线
                    adjustflag="2",  # 前复权
                )

                if rs is None or rs.error_code != "0":
                    logger.warning(f"获取数据失败: {rs.error_msg}")
                    return None

                # 转换结果为 DataFrame
                data_list = []
                while rs.next():
                    data_list.append(rs.get_row_data())

                df = pd.DataFrame(data_list, columns=rs.fields)
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

        # 列名映射（只需要处理 pctChg）
        column_mapping = {"pctChg": "pct_chg"}
        df.rename(columns=column_mapping, inplace=True)

        # 数值类型转换（Baostock 返回的都是字符串）
        numeric_cols = ["open", "high", "low", "close", "volume", "amount", "pct_chg"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

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

        Baostock 不支持实时行情（T+1 延迟），返回 None

        Args:
            symbol: 股票代码

        Returns:
            None（不支持）
        """
        # Baostock 数据有延迟，不支持实时行情
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
    def _baostock_session(self) -> Generator:
        """
        Baostock 会话上下文管理器

        确保：
        1. 进入上下文时自动登录
        2. 退出上下文时自动登出
        3. 异常时也能正确登出
        """
        bs = self._get_baostock()
        if bs is None:
            raise ImportError("baostock 库未安装")

        login_result = None

        try:
            # 登录 Baostock
            login_result = bs.login()

            if login_result is None or login_result.error_code != "0":
                raise ConnectionError(
                    f"Baostock 登录失败: {login_result.error_msg if login_result else 'Unknown error'}"
                )

            logger.debug("Baostock 登录成功")
            yield bs

        finally:
            # 确保登出，防止连接泄露
            try:
                logout_result = bs.logout()
                if logout_result is not None and logout_result.error_code == "0":
                    logger.debug("Baostock 登出成功")
                else:
                    logger.warning(
                        f"Baostock 登出异常: {logout_result.error_msg if logout_result else 'Unknown'}"
                    )
            except Exception as e:
                logger.warning(f"Baostock 登出时发生错误: {e}")

    # ==================== 工具方法 ====================

    @staticmethod
    def _get_baostock():
        """获取 baostock 模块"""
        return bs

    def _convert_stock_code(self, stock_code: str) -> str:
        """
        转换股票代码格式

        Baostock 格式：sh.600519 或 sz.000001

        Args:
            stock_code: 标准股票代码（600519）

        Returns:
            Baostock 格式代码（sh.600519）
        """
        code = stock_code.strip()

        # 已经包含前缀的情况
        if code.startswith(("sh.", "sz.")):
            return code.lower()

        # 去除可能的后缀
        code = code.replace(".SH", "").replace(".SZ", "").replace(".sh", "").replace(".sz", "")

        # ETF 处理
        if len(code) == 6:
            if code.startswith(("51", "52", "56", "58")):
                return f"sh.{code}"  # 上海 ETF
            if code.startswith(("15", "16", "18")):
                return f"sz.{code}"  # 深圳 ETF

        # 根据代码前缀判断市场
        if code.startswith(("600", "601", "603", "688")):
            return f"sh.{code}"  # 上海主板
        elif code.startswith(("000", "002", "300")):
            return f"sz.{code}"  # 深圳主板/中小板/创业板
        else:
            logger.warning(f"无法确定股票 {code} 的市场，默认使用深市")
            return f"sz.{code}"

    @staticmethod
    def _is_us_code(stock_code: str) -> bool:
        """判断代码是否为美股"""
        code = stock_code.strip().upper()
        return bool(re.match(r"^[A-Z]{1,5}(\.[A-Z])?$", code))

    @staticmethod
    def _parse_market_type(bs_code: str) -> str:
        """根据 Baostock 代码解析市场类型"""
        code = bs_code.replace("sh.", "").replace("sz.", "")

        if code.startswith("688"):
            return "科创板"
        elif code.startswith("300"):
            return "创业板"
        elif code.startswith("002"):
            return "中小板"
        elif code.startswith(("600", "601", "603")):
            return "主板"
        elif code.startswith("000"):
            return "主板"
        else:
            return "其他"
