"""
数据源管理器

集中多数据源调度逻辑，按优先级顺序尝试各数据源。
支持按市场（A股/美股）管理不同的数据源。
"""

import re
import time
from typing import List, Optional, Tuple, Dict, Any, Callable
import pandas as pd

from .stock_list import StockListService


class CircuitBreaker:
    """
    熔断器

    管理单个数据源的熔断状态

    状态流转：
    CLOSED（正常） --失败N次--> OPEN（熔断）--冷却时间到--> HALF_OPEN（半开）
    HALF_OPEN --成功--> CLOSED
    HALF_OPEN --失败--> OPEN
    """

    # 状态常量
    CLOSED = "closed"  # 正常状态
    OPEN = "open"  # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态

    def __init__(
        self,
        failure_threshold: int = 3,
        cooldown_seconds: float = 300.0,
    ):
        """
        初始化熔断器

        Args:
            failure_threshold: 连续失败次数阈值，达到后触发熔断
            cooldown_seconds: 熔断冷却时间（秒）
        """
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds

        # 状态
        self._state = self.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None

    @property
    def state(self) -> str:
        """当前状态"""
        return self._state

    def is_available(self) -> bool:
        """
        检查数据源是否可用

        Returns:
            True - 可以尝试请求
            False - 应跳过该数据源
        """
        if self._state == self.CLOSED:
            return True

        if self._state == self.OPEN:
            # 检查冷却时间
            if self._last_failure_time is None:
                return True

            elapsed = time.time() - self._last_failure_time
            if elapsed >= self.cooldown_seconds:
                # 冷却完成，进入半开状态
                self._state = self.HALF_OPEN
                return True
            return False

        if self._state == self.HALF_OPEN:
            return True

        return True

    def record_success(self):
        """记录成功请求"""
        # 任何状态成功都恢复到正常状态
        self._state = self.CLOSED
        self._failure_count = 0

    def record_failure(self):
        """记录失败请求"""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == self.HALF_OPEN:
            # 半开状态失败，重新熔断
            self._state = self.OPEN
        elif self._failure_count >= self.failure_threshold:
            # 达到阈值，进入熔断
            self._state = self.OPEN

    def reset(self):
        """重置熔断器状态"""
        self._state = self.CLOSED
        self._failure_count = 0
        self._last_failure_time = None


class DataManager:
    """
    数据源管理器

    职责：
    1. 管理多个数据源（按市场分类，按优先级排序）
    2. 自动故障切换
    3. 熔断机制
    4. 提供统一的数据获取接口
    """

    # 支持的市场
    MARKET_CN = "CN"
    MARKET_US = "US"

    def __init__(
        self,
        fetchers: Optional[List] = None,
        failure_threshold: int = 3,
        cooldown_seconds: float = 300.0,
        fetchers_by_market: Optional[Dict[str, List]] = None,
    ):
        """
        初始化管理器

        Args:
            fetchers: 数据源实例列表（单个市场使用）
            failure_threshold: 熔断失败次数阈值
            cooldown_seconds: 熔断冷却时间（秒）
            fetchers_by_market: 按市场分类的数据源字典 {"CN": [...], "US": [...]}
        """
        # 支持按市场管理 fetchers
        if fetchers_by_market:
            self._fetchers_by_market: Dict[str, List] = {}
            for market, fetcher_list in fetchers_by_market.items():
                self._fetchers_by_market[market] = sorted(fetcher_list, key=lambda f: f.priority)
        elif fetchers:
            # 兼容旧的单列表方式
            self._fetchers_by_market = {"CN": sorted(fetchers, key=lambda f: f.priority)}
        else:
            self._fetchers_by_market = {}

        # 每个 Fetcher 的熔断器
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._failure_threshold = failure_threshold
        self._cooldown_seconds = cooldown_seconds
        self._init_circuit_breakers()

    def _init_circuit_breakers(self):
        """初始化所有熔断器"""
        self._circuit_breakers = {}
        for market, fetchers in self._fetchers_by_market.items():
            for fetcher in fetchers:
                key = f"{market}_{fetcher.SOURCE_NAME}"
                if key not in self._circuit_breakers:
                    self._circuit_breakers[key] = CircuitBreaker(
                        failure_threshold=self._failure_threshold,
                        cooldown_seconds=self._cooldown_seconds,
                    )

    @staticmethod
    def _get_market(symbol: str) -> str:
        """根据股票代码判断市场"""
        symbol = str(symbol).strip().upper()
        if re.search(r"[A-Za-z]", symbol):
            return DataManager.MARKET_US
        return DataManager.MARKET_CN

    @staticmethod
    def create_market_manager(
        cn_fetchers: List,
        us_fetchers: List,
        failure_threshold: int = 3,
        cooldown_seconds: float = 300.0,
    ) -> "DataManager":
        """
        工厂方法：创建支持多市场的 DataManager

        Args:
            cn_fetchers: A股数据源列表
            us_fetchers: 美股数据源列表
            failure_threshold: 熔断失败次数阈值
            cooldown_seconds: 熔断冷却时间（秒）

        Returns:
            DataManager 实例
        """
        return DataManager(
            fetchers_by_market={
                DataManager.MARKET_CN: cn_fetchers,
                DataManager.MARKET_US: us_fetchers,
            },
            failure_threshold=failure_threshold,
            cooldown_seconds=cooldown_seconds,
        )

    def _get_fetchers(self, market: str) -> List:
        """获取指定市场的数据源列表"""
        return self._fetchers_by_market.get(market, [])

    def _get_circuit_breaker(self, market: str, source_name: str) -> CircuitBreaker:
        """获取指定市场和数据源的熔断器"""
        key = f"{market}_{source_name}"
        if key not in self._circuit_breakers:
            self._circuit_breakers[key] = CircuitBreaker(
                failure_threshold=self._failure_threshold,
                cooldown_seconds=self._cooldown_seconds,
            )
        return self._circuit_breakers[key]

    def add_fetcher(self, fetcher, market: Optional[str] = None):
        """
        添加数据源并重新排序

        Args:
            fetcher: 数据源实例
            market: 市场类型 ("CN" 或 "US")，如果不指定则尝试自动判断
        """
        if market is None:
            # 尝试从 fetcher 的 is_available 方法判断
            if hasattr(fetcher, "is_available"):
                if fetcher.is_available("A股"):
                    market = self.MARKET_CN
                elif fetcher.is_available("美股"):
                    market = self.MARKET_US

        if market is None:
            market = self.MARKET_CN  # 默认 A 股

        if market not in self._fetchers_by_market:
            self._fetchers_by_market[market] = []

        self._fetchers_by_market[market].append(fetcher)
        self._fetchers_by_market[market].sort(key=lambda f: f.priority)

        # 添加熔断器
        key = f"{market}_{fetcher.SOURCE_NAME}"
        self._circuit_breakers[key] = CircuitBreaker(
            failure_threshold=self._failure_threshold,
            cooldown_seconds=self._cooldown_seconds,
        )

    @property
    def available_sources(self) -> List[str]:
        """返回可用数据源名称列表"""
        sources = []
        for fetchers in self._fetchers_by_market.values():
            sources.extend([f.SOURCE_NAME for f in fetchers])
        return sources

    def get_circuit_breaker_status(self) -> Dict[str, str]:
        """返回所有数据源的熔断状态"""
        return {name: cb.state for name, cb in self._circuit_breakers.items()}

    # ==================== 新增方法 ====================

    def get_stock_daily(self, symbol: str) -> Tuple[Optional[pd.DataFrame], str, str]:
        """
        统一入口：获取 [日线数据]、[股票名称] 和 [数据源]
        按市场自动分发到对应的数据源

        :param symbol: 股票代码 (如 "600519", "NVDA")
        :return: (DataFrame, stock_name, data_source)
                 如果数据获取失败，DataFrame 为 None, name 为 symbol, data_source 为 ""
        """
        try:
            symbol = str(symbol).strip().upper()
            stock_name = symbol
            data_source = ""
            df = None

            # 判断市场并分发
            market = self._get_market(symbol)

            if market == self.MARKET_US:
                # 美股
                try:
                    stock_name = self._get_us_name(symbol)
                except Exception:
                    pass
                df, source = self.get_daily_data(symbol)
                data_source = f"US_{source}" if source else ""
            else:
                # A股
                try:
                    stock_name = self._get_cn_name(symbol)
                except Exception:
                    pass
                df, source = self.get_daily_data(symbol)
                data_source = f"CN_{source}" if source else ""

            return df, stock_name, data_source
        except Exception as e:
            print(f"❌ get_stock_daily 异常: {e}")
            fallback_symbol = str(symbol).strip().upper() if symbol else "UNKNOWN"
            return None, fallback_symbol, ""

    def _get_cn_name(self, symbol: str) -> str:
        """获取A股名称（从缓存的股票列表读取）"""
        try:
            stocks = StockListService.get_a_stock_list()
            for stock in stocks:
                if stock.get("symbol") == symbol:
                    name = stock.get("name")
                    if name:
                        return str(name)
        except Exception as e:
            print(f"⚠️ 从缓存获取A股名称失败: {e}")
        return symbol

    def _get_us_name(self, symbol: str) -> str:
        """获取美股名称（从缓存的股票列表读取）"""
        try:
            stocks = StockListService.get_us_stock_list()
            for stock in stocks:
                if stock.get("symbol") == symbol:
                    name = stock.get("name")
                    if name:
                        return str(name)
        except Exception as e:
            print(f"⚠️ 从缓存获取美股名称失败: {e}")
        return symbol

    def get_stock_info(self, symbol: str) -> dict:
        """获取股票基本信息（名称和行业）"""
        symbol = str(symbol).strip().upper()
        info = {"name": symbol, "industry": ""}

        try:
            market = self._get_market(symbol)
            stocks = (
                StockListService.get_us_stock_list()
                if market == self.MARKET_US
                else StockListService.get_a_stock_list()
            )

            for stock in stocks:
                if stock.get("symbol") == symbol:
                    info["name"] = stock.get("name", symbol)
                    info["industry"] = stock.get("industry", "")
                    break
        except Exception as e:
            print(f"⚠️ 获取股票信息失败: {e}")

        return info

    # ==================== 通用调度方法 ====================

    def _execute_with_fallback(
        self,
        market: str,
        fetchers: List,
        call: Callable,
        is_empty: Callable = lambda x: x is None,
        preprocess: Callable = lambda x: x,
        log_prefix: str = "",
    ) -> Tuple[Optional[Any], str]:
        """
        通用执行方法：统一降级与熔断策略

        熔断规则：
        - 每个 Fetcher 独立 failure_count
        - 达到阈值进入 cooldown

        降级规则：
        - 某 Fetcher 失败 → 尝试下一个
        - 全部失败 → 返回 None（不抛异常）

        Args:
            market: 市场类型 ("CN" 或 "US")
            fetchers: 数据源列表（按优先级排序）
            call: 调用 fetcher 的函数，签名为 call(fetcher) -> result
            is_empty: 判断结果是否为空的函数，默认为 None 则认为 None 是空
            preprocess: 预处理结果的函数，签名为 preprocess(result) -> result
            log_prefix: 日志前缀

        Returns:
            (result, source_name) - 成功
            (None, "") - 全部失败
        """
        errors = []
        total = len(fetchers)

        for i, fetcher in enumerate(fetchers):
            source_name = fetcher.SOURCE_NAME
            circuit_breaker = self._get_circuit_breaker(market, source_name)

            # 检查熔断状态
            if not circuit_breaker.is_available():
                print(f"  [{i+1}/{total}] {source_name} 熔断中，跳过")
                errors.append(f"[{source_name}] 熔断中，跳过")
                continue

            try:
                print(f"  [{i+1}/{total}] 尝试 {source_name}...")
                result = call(fetcher)

                if is_empty(result):
                    # 空数据，视为失败
                    circuit_breaker.record_failure()
                    errors.append(f"[{source_name}] 返回空数据")
                    continue

                # 成功，重置熔断状态
                circuit_breaker.record_success()
                processed = preprocess(result)
                return processed, source_name

            except Exception as e:
                # 异常，记录失败
                circuit_breaker.record_failure()
                errors.append(f"[{source_name}] {e}")

        # 全部失败
        if errors:
            print(f"❌ {log_prefix} 数据获取全失败: {'; '.join(errors)}")
        return None, ""

    # ==================== 现有方法（统一使用 _execute_with_fallback）====================

    def get_daily_data(self, symbol: str) -> Tuple[Optional[pd.DataFrame], str]:
        """
        获取日线数据（自动切换数据源 + 熔断）

        根据股票代码自动判断市场并分发。

        Args:
            symbol: 股票代码

        Returns:
            (DataFrame, source_name) - 成功
            (None, "") - 全部失败
        """
        market = self._get_market(symbol)
        fetchers = self._get_fetchers(market)

        if market == self.MARKET_CN:
            print(f"正在获取 A股数据: [{symbol}]")
            log_prefix = "A股"
        else:
            print(f"正在获取 美股数据: [{symbol}]")
            log_prefix = "美股"

        return self._execute_with_fallback(
            market=market,
            fetchers=fetchers,
            call=lambda f: f.get_daily_data(symbol),
            is_empty=lambda x: x is None or (hasattr(x, "empty") and x.empty),
            log_prefix=log_prefix,
        )

    def get_financial_data(self, symbol: str) -> Tuple[Optional[dict], str]:
        """
        获取财务数据（自动切换数据源 + 熔断）

        根据股票代码自动判断市场并分发。

        Args:
            symbol: 股票代码

        Returns:
            (financial_data, source_name)
        """
        market = self._get_market(symbol)
        fetchers = self._get_fetchers(market)

        if market == self.MARKET_CN:
            print(f"正在获取 A股财务数据: [{symbol}]")
            # A股：尝试 get_cn_financial_data
            call = lambda f: (
                f.get_cn_financial_data(symbol)[0] if hasattr(f, "get_cn_financial_data") else None
            )
        else:
            print(f"正在获取 美股财务数据: [{symbol}]")
            # 美股：尝试 get_us_financial_data
            call = lambda f: (
                f.get_us_financial_data(symbol)[0] if hasattr(f, "get_us_financial_data") else None
            )

        return self._execute_with_fallback(
            market=market,
            fetchers=fetchers,
            call=call,
            is_empty=lambda x: x is None or x == {},
            log_prefix=f"{market}财务",
        )

    def reset_circuit_breaker(self, source_name: str):
        """重置指定数据源的熔断器"""
        if source_name in self._circuit_breakers:
            self._circuit_breakers[source_name].reset()

    def reset_all_circuit_breakers(self):
        """重置所有熔断器"""
        for cb in self._circuit_breakers.values():
            cb.reset()
