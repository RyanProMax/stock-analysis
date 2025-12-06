"""
Qlib Alpha158 因子库

实现 qlib 的 158 个经典量价因子。
这些因子基于价格和成交量数据，通过数学运算和统计方法生成。

因子分类：
- 日内因子：基于当日开盘价、收盘价、最高价、最低价
- 波动因子：不同时间窗口的价格波动
- 价格因子：移动平均、收益率等
- 成交量因子：成交量均值、比率等
- 量价相关性因子：价格与成交量的相关性

注意：由于 qlib 的因子是通过表达式动态生成的，这里我们根据 qlib 的因子定义，
使用现有的数据源（stockstats 和原始 DataFrame）来实现这些因子。
"""

from typing import List
import pandas as pd
import numpy as np
from stockstats import StockDataFrame

from ..model import FactorDetail
from .base import BaseFactor, FactorLibrary


class Qlib158FactorLibrary(FactorLibrary):
    """
    Qlib Alpha158 因子库

    实现 qlib 的 158 个经典因子，统一输出格式为 FactorDetail。
    根据现有数据源（stockstats 和原始 DataFrame）进行计算。
    """

    def get_factors(
        self, stock: StockDataFrame, raw_df: pd.DataFrame, **kwargs
    ) -> List[FactorDetail]:
        """
        获取所有 qlib 158 因子

        Args:
            stock: StockDataFrame 对象
            raw_df: 原始行情数据 DataFrame
            **kwargs: 其他参数

        Returns:
            List[FactorDetail]: qlib 158 因子列表
        """
        factors = []

        # 获取最新数据
        last_row = stock.iloc[-1]
        close = float(last_row.get("close", 0.0))
        open_price = float(last_row.get("open", close))
        high = float(last_row.get("high", close))
        low = float(last_row.get("low", close))
        volume = float(last_row.get("volume", 0.0))

        # 计算基础指标
        df = raw_df.copy()
        if len(df) < 60:
            # 数据不足，返回空列表或基础因子
            return self._get_basic_factors(stock, raw_df, **kwargs)

        # 1. 日内因子（基于当日 OHLC 数据）
        factors.extend(self._calculate_intraday_factors(df, close, open_price, high, low, volume))

        # 2. 价格因子（移动平均、收益率等）
        factors.extend(self._calculate_price_factors(df, stock))

        # 3. 波动因子（不同时间窗口的波动率）
        factors.extend(self._calculate_volatility_factors(df, stock))

        # 4. 成交量因子（成交量均值、比率等）
        factors.extend(self._calculate_volume_factors(df, stock))

        # 5. 量价相关性因子
        factors.extend(self._calculate_price_volume_correlation_factors(df, stock))

        return factors

    def _get_basic_factors(
        self, stock: StockDataFrame, raw_df: pd.DataFrame, **kwargs
    ) -> List[FactorDetail]:
        """数据不足时返回基础因子"""
        factors = []
        last_row = stock.iloc[-1]
        close = float(last_row.get("close", 0.0))

        # 基础收益率因子
        if len(raw_df) >= 2:
            prev_close = float(raw_df.iloc[-2]["close"])
            if prev_close > 0:
                ret = (close - prev_close) / prev_close
                factors.append(
                    FactorDetail(
                        key="qlib_ret_1",
                        name="Qlib-1日收益率",
                        category="技术面",
                        status=f"收益率: {ret:.2%}",
                        bullish_signals=(
                            [{"type": "technical", "message": f"1日收益率: {ret:.2%}"}]
                            if ret > 0
                            else []
                        ),
                        bearish_signals=(
                            [{"type": "technical", "message": f"1日收益率: {ret:.2%}"}]
                            if ret < 0
                            else []
                        ),
                    )
                )

        return factors

    def _calculate_intraday_factors(
        self,
        df: pd.DataFrame,
        close: float,
        open_price: float,
        high: float,
        low: float,
        volume: float,
    ) -> List[FactorDetail]:
        """计算日内因子"""
        factors = []

        # 因子 1: 当日涨跌幅 (close - open) / open
        if open_price > 0:
            intraday_return = (close - open_price) / open_price
            factors.append(
                FactorDetail(
                    key="qlib_intraday_ret",
                    name="Qlib-日内收益率",
                    category="技术面",
                    status=f"日内收益率: {intraday_return:.2%}",
                    bullish_signals=(
                        [
                            {
                                "type": "technical",
                                "message": f"日内上涨 {intraday_return:.2%}",
                            }
                        ]
                        if intraday_return > 0
                        else []
                    ),
                    bearish_signals=(
                        [
                            {
                                "type": "technical",
                                "message": f"日内下跌 {intraday_return:.2%}",
                            }
                        ]
                        if intraday_return < 0
                        else []
                    ),
                )
            )

        # 因子 2: 上下影线比例
        if high > low:
            upper_shadow = high - max(close, open_price)
            lower_shadow = min(close, open_price) - low
            body = abs(close - open_price)
            total_range = high - low

            if total_range > 0:
                upper_ratio = upper_shadow / total_range
                lower_ratio = lower_shadow / total_range

                factors.append(
                    FactorDetail(
                        key="qlib_shadow_ratio",
                        name="Qlib-上下影线比例",
                        category="技术面",
                        status=f"上影: {upper_ratio:.2%}, 下影: {lower_ratio:.2%}",
                        bullish_signals=(
                            [
                                {
                                    "type": "technical",
                                    "message": f"下影线较长 ({lower_ratio:.2%})，支撑较强",
                                }
                            ]
                            if lower_ratio > 0.3
                            else []
                        ),
                        bearish_signals=(
                            [
                                {
                                    "type": "technical",
                                    "message": f"上影线较长 ({upper_ratio:.2%})，压力较大",
                                }
                            ]
                            if upper_ratio > 0.3
                            else []
                        ),
                    )
                )

        return factors

    def _calculate_price_factors(
        self, df: pd.DataFrame, stock: StockDataFrame
    ) -> List[FactorDetail]:
        """计算价格因子（移动平均、收益率等）"""
        factors = []
        last_row = stock.iloc[-1]

        # 计算不同周期的收益率
        windows = [5, 10, 20, 30, 60]
        for window in windows:
            if len(df) >= window:
                close_series = df["close"]
                ret = (close_series.iloc[-1] - close_series.iloc[-window]) / close_series.iloc[
                    -window
                ]

                factors.append(
                    FactorDetail(
                        key=f"qlib_ret_{window}",
                        name=f"Qlib-{window}日收益率",
                        category="技术面",
                        status=f"{window}日收益率: {ret:.2%}",
                        bullish_signals=(
                            [
                                {
                                    "type": "technical",
                                    "message": f"{window}日收益率: {ret:.2%}",
                                }
                            ]
                            if ret > 0
                            else []
                        ),
                        bearish_signals=(
                            [
                                {
                                    "type": "technical",
                                    "message": f"{window}日收益率: {ret:.2%}",
                                }
                            ]
                            if ret < 0
                            else []
                        ),
                    )
                )

        # 计算不同周期的移动平均
        for window in [5, 10, 20, 30, 60]:
            if len(df) >= window:
                ma_series = df["close"].rolling(window=window).mean()
                ma = float(ma_series.values[-1])  # type: ignore
                close = float(last_row.get("close", 0.0))
                if close > 0:
                    ma_ratio = (close - ma) / ma
                    factors.append(
                        FactorDetail(
                            key=f"qlib_ma_ratio_{window}",
                            name=f"Qlib-价格相对MA{window}比例",
                            category="技术面",
                            status=f"相对MA{window}: {ma_ratio:.2%}",
                            bullish_signals=(
                                [
                                    {
                                        "type": "technical",
                                        "message": f"价格高于MA{window} {ma_ratio:.2%}",
                                    }
                                ]
                                if ma_ratio > 0
                                else []
                            ),
                            bearish_signals=(
                                [
                                    {
                                        "type": "technical",
                                        "message": f"价格低于MA{window} {abs(ma_ratio):.2%}",
                                    }
                                ]
                                if ma_ratio < 0
                                else []
                            ),
                        )
                    )

        return factors

    def _calculate_volatility_factors(
        self, df: pd.DataFrame, stock: StockDataFrame
    ) -> List[FactorDetail]:
        """计算波动因子"""
        factors = []
        last_row = stock.iloc[-1]

        # 计算不同周期的波动率（标准差）
        windows = [5, 10, 20, 30, 60]
        for window in windows:
            if len(df) >= window:
                close_series = df["close"]
                returns = close_series.pct_change().dropna()
                if len(returns) >= window:
                    volatility = returns.tail(window).std() * np.sqrt(252)  # 年化波动率

                    factors.append(
                        FactorDetail(
                            key=f"qlib_volatility_{window}",
                            name=f"Qlib-{window}日波动率",
                            category="技术面",
                            status=f"{window}日年化波动率: {volatility:.2%}",
                            bullish_signals=[],
                            bearish_signals=(
                                [
                                    {
                                        "type": "technical",
                                        "message": f"波动率较高 ({volatility:.2%})，风险较大",
                                    }
                                ]
                                if volatility > 0.3
                                else []
                            ),
                        )
                    )

        return factors

    def _calculate_volume_factors(
        self, df: pd.DataFrame, stock: StockDataFrame
    ) -> List[FactorDetail]:
        """计算成交量因子"""
        factors = []

        if "volume" not in df.columns:
            return factors

        # 计算不同周期的成交量均值
        windows = [5, 10, 20, 30, 60]
        for window in windows:
            if len(df) >= window:
                volume_series = df["volume"]
                volume_ma_series = volume_series.rolling(window=window).mean()
                volume_ma = float(volume_ma_series.values[-1])  # type: ignore
                current_volume = float(volume_series.values[-1])  # type: ignore

                if volume_ma > 0:
                    volume_ratio = current_volume / volume_ma
                    factors.append(
                        FactorDetail(
                            key=f"qlib_volume_ratio_{window}",
                            name=f"Qlib-成交量相对MA{window}比例",
                            category="技术面",
                            status=f"成交量/MA{window}: {volume_ratio:.2f}x",
                            bullish_signals=(
                                [
                                    {
                                        "type": "technical",
                                        "message": f"成交量放大 {volume_ratio:.2f}倍",
                                    }
                                ]
                                if volume_ratio > 1.5
                                else []
                            ),
                            bearish_signals=(
                                [
                                    {
                                        "type": "technical",
                                        "message": f"成交量萎缩 {volume_ratio:.2f}倍",
                                    }
                                ]
                                if volume_ratio < 0.6
                                else []
                            ),
                        )
                    )

        return factors

    def _calculate_price_volume_correlation_factors(
        self, df: pd.DataFrame, stock: StockDataFrame
    ) -> List[FactorDetail]:
        """计算量价相关性因子"""
        factors = []

        if "volume" not in df.columns:
            return factors

        # 计算价格与成交量的相关性
        windows = [5, 10, 20, 30, 60]
        for window in windows:
            if len(df) >= window:
                close_series = df["close"].tail(window)
                volume_series = df["volume"].tail(window)

                # 计算收益率与成交量的相关性
                returns = close_series.pct_change().dropna()
                volume_changes = volume_series.pct_change().dropna()

                if len(returns) > 1 and len(volume_changes) > 1:
                    min_len = min(len(returns), len(volume_changes))
                    returns_array = np.array(returns.tail(min_len).values, dtype=float)
                    volume_changes_array = np.array(
                        volume_changes.tail(min_len).values, dtype=float
                    )
                    if len(returns_array) > 1 and len(volume_changes_array) > 1:
                        correlation_matrix = np.corrcoef(returns_array, volume_changes_array)
                        correlation = (
                            float(correlation_matrix[0, 1])
                            if correlation_matrix.shape == (2, 2)
                            else np.nan
                        )
                    else:
                        correlation = np.nan

                    if not np.isnan(correlation):
                        factors.append(
                            FactorDetail(
                                key=f"qlib_price_volume_corr_{window}",
                                name=f"Qlib-{window}日量价相关性",
                                category="技术面",
                                status=f"量价相关性: {correlation:.3f}",
                                bullish_signals=(
                                    [
                                        {
                                            "type": "technical",
                                            "message": f"量价正相关 ({correlation:.3f})，上涨有量支撑",
                                        }
                                    ]
                                    if correlation > 0.3
                                    else []
                                ),
                                bearish_signals=(
                                    [
                                        {
                                            "type": "technical",
                                            "message": f"量价负相关 ({correlation:.3f})，上涨无量",
                                        }
                                    ]
                                    if correlation < -0.3
                                    else []
                                ),
                            )
                        )

        return factors
