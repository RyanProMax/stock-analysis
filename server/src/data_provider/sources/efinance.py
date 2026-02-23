"""
Efinance 数据源

使用 efinance（东方财富）获取 A 股股票列表、日线数据、实时行情

特点：
- 免费，无需 Token
- 支持实时行情
- 支持 ETF 基金
- 内置防封禁策略（Jitter + UA 轮换 + 指数退避）
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import efinance as ef
import time
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import logging

from ..base import BaseStockDataSource
from ..realtime_types import UnifiedRealtimeQuote, RealtimeSource


logger = logging.getLogger(__name__)


class EfinanceDataSource(BaseStockDataSource):
    """Efinance 数据源（东方财富）"""

    SOURCE_NAME: str = "Efinance"
    priority: int = 0  # A股最高优先级

    # 列名��射（efinance 中文列名 -> 标准英文列名）
    COLUMN_MAPPING = {
        "日期": "date",
        "开盘": "open",
        "收盘": "close",
        "最高": "high",
        "最低": "low",
        "成交量": "volume",
        "成交额": "amount",
        "涨跌幅": "pct_chg",
        "股票代码": "code",
        "股票名称": "name",
        # ETF 基金可能的列名
        "基金代码": "code",
        "基金名称": "name",
        "单位净值": "close",
    }

    # 请求速率限制（秒）
    MIN_SLEEP: float = 1.5
    MAX_SLEEP: float = 3.0

    def __init__(self):
        super().__init__()
        self._last_request_time: Optional[float] = None

    # ==================== 股票列表 ====================

    def fetch_a_stocks(self) -> List[Dict[str, Any]]:
        """获取 A 股股票列表"""
        try:
            self._enforce_rate_limit()

            df = ef.stock.get_realtime_quotes()  # 获取实时行情数据
            if df is None or df.empty:
                return []

            stocks = []
            code_col = "股票代码" if "股票代码" in df.columns else "code"
            name_col = "股票名称" if "股票名称" in df.columns else "name"

            for _, row in df.iterrows():
                symbol = str(row[code_col]).strip()
                name = str(row.get(name_col, "")).strip()

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

        except ImportError:
            print("⚠️ efinance 未安装，跳过 EfinanceDataSource")
            return []
        except Exception as e:
            logger.warning(f"获取A股列表失败: {e}")
            return []

    def fetch_us_stocks(self) -> List[Dict[str, Any]]:
        """Efinance 不支持美股列表"""
        return []

    # ==================== 日线数据 ====================

    @retry(
        stop=stop_after_attempt(1),  # 减少到1次，避免触发限流
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((ConnectionError, TimeoutError, Exception)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def _fetch_raw_daily(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        获取原始日线数据

        Args:
            symbol: 股票代码（支持 A 股和 ETF）

        Returns:
            原始 DataFrame，失败返回 None
        """
        try:
            self._enforce_rate_limit()

            # 判断是否为 ETF 代码
            if self._is_etf_code(symbol):
                return self._fetch_etf_data(symbol)
            else:
                return self._fetch_stock_data(symbol)

        except ImportError:
            print("⚠️ efinance 未安装")
            return None
        except Exception as e:
            # 检测反爬封禁
            error_msg = str(e).lower()
            if any(
                keyword in error_msg for keyword in ["banned", "blocked", "频率", "rate", "限制"]
            ):
                logger.warning(f"检测到可能被封禁: {e}")
            raise

    def _fetch_stock_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """获取普通股票日线数据"""
        try:
            # 获取最近 2 年数据
            from datetime import datetime, timedelta

            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=730)).strftime("%Y%m%d")

            result = ef.stock.get_quote_history(
                stock_codes=symbol,
                beg=start_date,
                end=end_date,
                klt=101,  # 日线
                fqt=1,  # 前复权
            )

            # 处理可能的 Dict 返回值
            if result is None:
                return None
            if isinstance(result, dict):
                # 取第一个 DataFrame
                values = list(result.values())
                return values[0] if len(values) > 0 else None
            return result

        except Exception as e:
            logger.warning(f"获取股票 {symbol} 数据失败: {e}")
            return None

    def _fetch_etf_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """获取 ETF 基金日线数据"""
        try:
            # efinance ETF 接口不支持日期参数，需要手动过滤
            from datetime import datetime, timedelta

            end_date = datetime.now()
            start_date = end_date - timedelta(days=730)

            df = ef.fund.get_quote_history(fund_code=symbol)

            if df is not None and not df.empty and "日期" in df.columns:
                # 手动过滤日期
                df["日期"] = pd.to_datetime(df["日期"])
                mask = (df["日期"] >= start_date) & (df["日期"] <= end_date)
                df = df[mask].copy()

            return df

        except Exception as e:
            logger.warning(f"获取ETF {symbol} 数据失败: {e}")
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
        df.rename(columns=self.COLUMN_MAPPING, inplace=True)

        # 对于 ETF 数据（只有 close/单位净值），补全其他 OHLC 列
        if "close" in df.columns and "open" not in df.columns:
            df["open"] = df["close"]
            df["high"] = df["close"]
            df["low"] = df["close"]

        # 补全 volume 和 amount，如果缺失
        if "volume" not in df.columns:
            df["volume"] = 0
        if "amount" not in df.columns:
            df["amount"] = 0

        # 如果没有 code 列，手动添加
        if "code" not in df.columns:
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
        try:
            self._enforce_rate_limit()

            # ETF 使用单独的接口
            if self._is_etf_code(symbol):
                return self._get_etf_realtime_quote(symbol)

            # 获取实时行情数据
            df = ef.stock.get_realtime_quotes()

            if df is None or df.empty:
                logger.warning("未获取到实时行情数据")
                return None

            # 查找指定股票
            code_col = "股票代码" if "股票代码" in df.columns else "code"
            row = df[df[code_col] == symbol]

            if row.empty:
                logger.warning(f"未找到股票 {symbol} 的实时行情")
                return None

            row = row.iloc[0]

            # 动态检测列名（支持中英文）
            def _get_value(col_candidates: List[str], default=None):
                for col in col_candidates:
                    if col in row.index:
                        val = row[col]
                        if pd.notna(val):
                            return val
                return default

            # 获取各字段值
            name = _get_value(["股票名称", "name"], "")
            price = self._safe_float(_get_value(["最新价", "price"]))
            change_pct = self._safe_float(_get_value(["涨跌幅", "change_pct"]))
            change_amount = self._safe_float(_get_value(["涨跌额", "change"]))
            volume = self._safe_int(_get_value(["成交量", "volume"]))
            amount = self._safe_float(_get_value(["成交额", "amount"]))
            turnover_rate = self._safe_float(_get_value(["换手率", "turnover_rate"]))
            amplitude = self._safe_float(_get_value(["振幅", "amplitude"]))
            high = self._safe_float(_get_value(["最高", "high"]))
            low = self._safe_float(_get_value(["最低", "low"]))
            open_price = self._safe_float(_get_value(["开盘", "open"]))
            pre_close = self._safe_float(_get_value(["昨收", "pre_close"]))

            # 量比
            volume_ratio = self._safe_float(_get_value(["量比", "volume_ratio"]))

            # 估值指标
            pe_ratio = self._safe_float(_get_value(["市盈率", "pe"]))
            pb_ratio = self._safe_float(_get_value(["市净率", "pb"]))
            total_mv = self._safe_float(_get_value(["总市值", "total_mv"]))
            circ_mv = self._safe_float(_get_value(["流通市值", "circ_mv"]))

            return UnifiedRealtimeQuote(
                code=symbol,
                name=str(name),
                source=RealtimeSource.EFINANCE,
                price=price,
                change_pct=change_pct,
                change_amount=change_amount,
                volume=volume,
                amount=amount,
                turnover_rate=turnover_rate,
                amplitude=amplitude,
                high=high,
                low=low,
                open_price=open_price,
                pre_close=pre_close,
                volume_ratio=volume_ratio,
                pe_ratio=pe_ratio,
                pb_ratio=pb_ratio,
                total_mv=total_mv,
                circ_mv=circ_mv,
            )

        except ImportError:
            logger.warning("efinance 未安装")
            return None
        except Exception as e:
            logger.warning(f"获取 {symbol} 实时行情失败: {e}")
            return None

    def _get_etf_realtime_quote(self, symbol: str) -> Optional[UnifiedRealtimeQuote]:
        """获取 ETF 实时行情"""
        try:
            # 获取 ETF 实时行情
            df = ef.fund.get_quote_history(fund_code=symbol)

            if df is None or df.empty:
                return None

            # 取最新一行
            df = df.sort_values("日期", ascending=False)
            row = df.iloc[0]

            name_col = "基金名称" if "基金名称" in row.index else "name"
            price_col = "单位净值" if "单位净值" in row.index else "close"

            return UnifiedRealtimeQuote(
                code=symbol,
                name=str(row.get(name_col, "")),
                source=RealtimeSource.EFINANCE,
                price=self._safe_float(row.get(price_col)),
            )

        except Exception as e:
            logger.warning(f"获取ETF {symbol} 实时行情失败: {e}")
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

    # ==================== 工具方法 ====================

    def _enforce_rate_limit(self) -> None:
        """
        强制执行速率限制

        策略：
        1. 检查距离上次请求的时间间隔
        2. 如果间隔不足，补充休眠时间
        3. 然后再执行随机 jitter 休眠
        """
        if self._last_request_time is not None:
            elapsed = time.time() - self._last_request_time
            min_interval = self.MIN_SLEEP
            if elapsed < min_interval:
                additional_sleep = min_interval - elapsed
                logger.debug(f"补充休眠 {additional_sleep:.2f} 秒")
                time.sleep(additional_sleep)

        # 执行随机 jitter 休眠
        self.random_sleep(self.MIN_SLEEP, self.MAX_SLEEP)
        self._last_request_time = time.time()

    @staticmethod
    def _is_etf_code(symbol: str) -> bool:
        """判断是否为 ETF 代码"""
        # ETF 通常以 5 开头（上海）或 15/16 开头（深圳）
        symbol = symbol.strip().upper()
        return (
            symbol.startswith("5")
            or symbol.startswith("15")
            or symbol.startswith("16")
            or symbol.startswith("56")
            or symbol.startswith("159")
        )

    @staticmethod
    def _safe_float(value) -> Optional[float]:
        """安全转换为 float"""
        try:
            if pd.isna(value):
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_int(value) -> Optional[int]:
        """安全转换为 int"""
        try:
            if pd.isna(value):
                return None
            return int(float(value))
        except (TypeError, ValueError):
            return None
