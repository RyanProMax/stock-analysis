"""
Qlib Alpha158 因子库

直接使用 qlib 的 Alpha158 因子库，获取 158 个经典量价因子。
通过 qlib 的表达式引擎直接计算 Alpha158 定义的因子。
"""

from typing import List, Optional
import pandas as pd
import numpy as np
from stockstats import StockDataFrame

from ..core import FactorDetail
from .base import FactorLibrary

try:
    from qlib.contrib.data.handler import Alpha158DL

    QLIB_AVAILABLE = True
except ImportError:
    QLIB_AVAILABLE = False


class Qlib158FactorLibrary(FactorLibrary):
    """
    Qlib Alpha158 因子库

    直接使用 qlib 的 Alpha158 数据处理器获取 158 个因子。
    通过 qlib 的表达式引擎计算 Alpha158 定义的因子。
    """

    def __init__(self):
        """初始化 qlib 因子库"""
        if not QLIB_AVAILABLE:
            print("⚠️ qlib 未安装，无法使用 Alpha158 因子库")
            self.qlib_available = False
            self.factor_expressions = []
            self.factor_names = []
        else:
            self.qlib_available = True
            # 初始化 Alpha158 的因子表达式
            self._init_alpha158_expressions()

    def _init_alpha158_expressions(self):
        """初始化 Alpha158 的因子表达式"""
        try:
            # 从 Alpha158DL 获取因子表达式和名称
            conf = {
                "kbar": {},
                "price": {
                    "windows": [0],
                    "feature": ["OPEN", "HIGH", "LOW", "VWAP"],
                },
                "rolling": {},
            }
            result = Alpha158DL.get_feature_config(conf)
            if isinstance(result, tuple) and len(result) >= 2:
                self.factor_expressions = result[0]  # 因子表达式列表
                self.factor_names = result[1]  # 因子名称列表
                # print(f"✓ 成功加载 Alpha158 因子表达式，共 {len(self.factor_expressions)} 个因子")
            else:
                self.factor_expressions = []
                self.factor_names = []
                # print("⚠️ 无法获取 Alpha158 因子表达式")
        except Exception as e:
            print(f"⚠️ 初始化 Alpha158 因子表达式失败: {e}")
            self.factor_expressions = []
            self.factor_names = []

    def get_factors(
        self,
        stock: StockDataFrame,
        raw_df: pd.DataFrame,
        symbol: Optional[str] = None,
        data_source: str = "",
        raw_data: Optional[dict] = None,
        **kwargs,
    ) -> List[FactorDetail]:
        """
        获取所有 qlib 158 因子

        Args:
            stock: StockDataFrame 对象
            raw_df: 原始行情数据 DataFrame，需要包含 open, close, high, low, volume 列
            symbol: 股票代码（可选）
            data_source: 数据源标识
            raw_data: 原始数据
            **kwargs: 其他参数

        Returns:
            List[FactorDetail]: qlib 158 因子列表
        """
        if not self.qlib_available or len(self.factor_expressions) == 0:
            return []

        factors = []

        try:
            if raw_df is None or len(raw_df) < 60:
                return []

            # 使用 qlib 的表达式引擎直接计算 Alpha158 因子
            factors = self._calculate_alpha158_with_qlib(raw_df, symbol, data_source, raw_data)

        except Exception as e:
            import traceback

            print(f"⚠️ 计算 Qlib 158 因子失败: {e}")
            traceback.print_exc()

        return factors

    def _calculate_alpha158_with_qlib(
        self,
        df: pd.DataFrame,
        symbol: Optional[str] = None,
        data_source: str = "",
        raw_data: Optional[dict] = None,
    ) -> List[FactorDetail]:
        """
        使用 qlib 的 Alpha158 表达式引擎计算因子

        直接使用 qlib 的 Alpha158 类定义的表达式来计算因子。

        Args:
            df: 包含 open, close, high, low, volume 的 DataFrame
            symbol: 股票代码
            data_source: 数据源标识
            raw_data: 原始数据

        Returns:
            List[FactorDetail]: 因子列表
        """
        factors = []

        try:
            # 准备数据
            qlib_df = self._prepare_qlib_dataframe(df, symbol)

            if qlib_df is None or len(qlib_df) < 60:
                return factors

            # 计算每个因子
            for i, (factor_expr, factor_name) in enumerate(
                zip(self.factor_expressions, self.factor_names)
            ):
                try:
                    # 使用 qlib 的表达式引擎计算因子
                    factor_value = self._evaluate_qlib_expression(factor_expr, qlib_df)

                    if factor_value is not None and not np.isnan(factor_value):
                        # 转换为 FactorDetail
                        factor_detail = self._value_to_factor_detail(
                            factor_name.lower(),
                            factor_name,
                            factor_value,
                            data_source=data_source,
                        )
                        if factor_detail:
                            factors.append(factor_detail)
                except Exception as e:
                    # 单个因子计算失败，继续
                    continue

        except Exception as e:
            import traceback

            print(f"⚠️ 使用 qlib Alpha158 计算因子失败: {e}")
            traceback.print_exc()

        return factors

    def _prepare_qlib_dataframe(
        self, df: pd.DataFrame, symbol: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """
        准备 qlib 格式的 DataFrame

        Args:
            df: 原始 DataFrame
            symbol: 股票代码

        Returns:
            qlib 格式的 DataFrame
        """
        if df is None or df.empty:
            return None

        # 复制 DataFrame
        qlib_df = df.copy()

        # 确保有 datetime 列
        if "date" in qlib_df.columns:
            qlib_df["datetime"] = pd.to_datetime(qlib_df["date"])
        elif "datetime" not in qlib_df.columns:
            if isinstance(qlib_df.index, pd.DatetimeIndex):
                qlib_df["datetime"] = qlib_df.index
            else:
                qlib_df["datetime"] = pd.date_range(
                    end=pd.Timestamp.now(), periods=len(qlib_df), freq="D"
                )

        # 确保列名符合 qlib 要求（qlib 使用大写）
        column_mapping = {
            "open": "OPEN",
            "close": "CLOSE",
            "high": "HIGH",
            "low": "LOW",
            "volume": "VOLUME",
        }

        # 重命名列
        for old_col, new_col in column_mapping.items():
            if old_col in qlib_df.columns and new_col not in qlib_df.columns:
                qlib_df[new_col] = qlib_df[old_col]

        # 确保必要的列存在
        required_cols = ["OPEN", "CLOSE", "HIGH", "LOW", "VOLUME"]
        for col in required_cols:
            if col not in qlib_df.columns:
                return None

        # 计算VWAP (Volume Weighted Average Price)
        # VWAP = Sum((High + Low + Close) / 3 * Volume) / Sum(Volume)
        if "VWAP" not in qlib_df.columns:
            high_vals = np.array(qlib_df["HIGH"].values, dtype=float)
            low_vals = np.array(qlib_df["LOW"].values, dtype=float)
            close_vals = np.array(qlib_df["CLOSE"].values, dtype=float)
            typical_price = (high_vals + low_vals + close_vals) / 3
            typical_price_series = pd.Series(typical_price, index=qlib_df.index)
            volume_series = pd.Series(qlib_df["VOLUME"].values, index=qlib_df.index)
            qlib_df["VWAP"] = (
                typical_price_series * volume_series
            ).expanding().sum() / volume_series.expanding().sum()

        # 设置 datetime 为索引
        if "datetime" in qlib_df.columns:
            qlib_df = qlib_df.set_index("datetime").sort_index()

        return qlib_df

    def _evaluate_qlib_expression(
        self,
        expr_str: str,
        df: pd.DataFrame,
    ) -> Optional[float]:
        """
        使用 qlib 的表达式引擎计算因子值

        这里我们手动解析和计算 qlib 表达式。
        qlib 表达式使用 $close, $open 等变量，以及 Ref, Sum, Mean 等函数。

        Args:
            expr_str: 表达式字符串，例如 "($close-$open)/$open"
            df: DataFrame，包含 OPEN, CLOSE, HIGH, LOW, VOLUME 列

        Returns:
            因子值（最新一行的值）
        """
        try:
            # 由于 qlib 的表达式引擎需要完整的数据提供者，我们手动实现一个简化版本
            # 这里我们使用 pandas 和 numpy 来计算表达式

            # 准备数据
            close = df["CLOSE"].values
            open_price = df["OPEN"].values
            high = df["HIGH"].values
            low = df["LOW"].values
            volume = df["VOLUME"].values if "VOLUME" in df.columns else np.zeros(len(df))
            vwap = (
                df["VWAP"].values
                if "VWAP" in df.columns
                else (high.astype(float) + low.astype(float) + close.astype(float)) / 3
            )

            # 创建一个安全的执行环境
            safe_dict = {
                "__builtins__": {},
                "np": np,
                "pd": pd,
                "close": close,
                "open": open_price,
                "high": high,
                "low": low,
                "volume": volume,
                "vwap": vwap,
                "$close": close,
                "$open": open_price,
                "$high": high,
                "$low": low,
                "$volume": volume,
                "$vwap": vwap,
            }

            # 定义 qlib 表达式函数
            def Ref(series, n):
                """引用 n 天前的值"""
                if isinstance(series, np.ndarray):
                    result = np.full_like(series, np.nan)
                    if n >= 0:
                        result[n:] = series[:-n] if n > 0 else series
                    else:
                        result[:n] = series[-n:]
                    return result
                return series.shift(n) if hasattr(series, "shift") else series

            def Greater(a, b):
                """返回 a 和 b 中的较大值"""
                if isinstance(a, np.ndarray) and isinstance(b, np.ndarray):
                    return np.maximum(a, b)
                return np.maximum(a, b)

            def Less(a, b):
                """返回 a 和 b 中的较小值"""
                if isinstance(a, np.ndarray) and isinstance(b, np.ndarray):
                    return np.minimum(a, b)
                return np.minimum(a, b)

            def Sum(series, window):
                """滚动求和"""
                if isinstance(series, np.ndarray):
                    result = np.full_like(series, np.nan)
                    for i in range(window - 1, len(series)):
                        result[i] = np.sum(series[i - window + 1 : i + 1])
                    return result
                return series.rolling(window).sum()

            def Mean(series, window):
                """滚动均值（支持布尔数组）"""
                if isinstance(series, np.ndarray):
                    result = np.full_like(series, np.nan, dtype=float)
                    for i in range(window - 1, len(series)):
                        window_data = series[i - window + 1 : i + 1]
                        # 如果是布尔数组，转换为float再计算均值
                        if window_data.dtype == bool:
                            result[i] = np.mean(window_data.astype(float))
                        else:
                            result[i] = np.mean(window_data)
                    return result
                # 对于pandas Series，也支持布尔类型
                if hasattr(series, "dtype") and series.dtype == bool:
                    return series.rolling(window).mean()
                return series.rolling(window).mean()

            def Std(series, window):
                """滚动标准差"""
                if isinstance(series, np.ndarray):
                    result = np.full_like(series, np.nan)
                    for i in range(window - 1, len(series)):
                        result[i] = np.std(series[i - window + 1 : i + 1])
                    return result
                return series.rolling(window).std()

            def Abs(x):
                """绝对值"""
                return np.abs(x)

            def Max(series, window):
                """滚动最大值"""
                if isinstance(series, np.ndarray):
                    result = np.full_like(series, np.nan)
                    for i in range(window - 1, len(series)):
                        result[i] = np.max(series[i - window + 1 : i + 1])
                    return result
                return series.rolling(window).max()

            def Min(series, window):
                """滚动最小值"""
                if isinstance(series, np.ndarray):
                    result = np.full_like(series, np.nan)
                    for i in range(window - 1, len(series)):
                        result[i] = np.min(series[i - window + 1 : i + 1])
                    return result
                return series.rolling(window).min()

            def Log(x):
                """自然对数"""
                return np.log(np.maximum(x, 1e-10))  # 避免log(0)

            def Corr(series1, series2, window):
                """滚动相关系数"""
                if isinstance(series1, np.ndarray) and isinstance(series2, np.ndarray):
                    result = np.full_like(series1, np.nan)
                    for i in range(window - 1, len(series1)):
                        s1 = series1[i - window + 1 : i + 1]
                        s2 = series2[i - window + 1 : i + 1]
                        if len(s1) == window and len(s2) == window:
                            corr = np.corrcoef(s1, s2)[0, 1]
                            result[i] = corr if not np.isnan(corr) else 0
                    return result
                # 如果是pandas Series
                s1_series = pd.Series(series1) if not isinstance(series1, pd.Series) else series1
                s2_series = pd.Series(series2) if not isinstance(series2, pd.Series) else series2
                return s1_series.rolling(window).corr(s2_series)

            def Rank(series, window):
                """滚动排名（0-1之间）"""
                if isinstance(series, np.ndarray):
                    result = np.full_like(series, np.nan)
                    for i in range(window - 1, len(series)):
                        window_data = series[i - window + 1 : i + 1]
                        ranks = np.argsort(np.argsort(window_data))
                        result[i] = (
                            ranks[-1] / (len(window_data) - 1) if len(window_data) > 1 else 0.5
                        )
                    return result
                return series.rolling(window).apply(
                    lambda x: ((x.rank().iloc[-1] - 1) / (len(x) - 1) if len(x) > 1 else 0.5)
                )

            def Quantile(series, window, q):
                """滚动分位数"""
                if isinstance(series, np.ndarray):
                    result = np.full_like(series, np.nan)
                    for i in range(window - 1, len(series)):
                        window_data = series[i - window + 1 : i + 1]
                        result[i] = np.quantile(window_data, q)
                    return result
                return series.rolling(window).quantile(q)

            def IdxMax(series, window):
                """滚动窗口内最大值的索引位置（从窗口开始到当前位置的距离）"""
                if isinstance(series, np.ndarray):
                    result = np.full_like(series, np.nan)
                    for i in range(window - 1, len(series)):
                        window_data = series[i - window + 1 : i + 1]
                        max_idx = np.argmax(window_data)
                        result[i] = len(window_data) - 1 - max_idx  # 距离当前的位置
                    return result
                return series.rolling(window).apply(lambda x: len(x) - 1 - np.argmax(x.values))

            def IdxMin(series, window):
                """滚动窗口内最小值的索引位置（从窗口开始到当前位置的距离）"""
                if isinstance(series, np.ndarray):
                    result = np.full_like(series, np.nan)
                    for i in range(window - 1, len(series)):
                        window_data = series[i - window + 1 : i + 1]
                        min_idx = np.argmin(window_data)
                        result[i] = len(window_data) - 1 - min_idx  # 距离当前的位置
                    return result
                return series.rolling(window).apply(lambda x: len(x) - 1 - np.argmin(x.values))

            def Slope(series, window):
                """滚动线性回归斜率"""
                if isinstance(series, np.ndarray):
                    result = np.full_like(series, np.nan)
                    x = np.arange(window)
                    for i in range(window - 1, len(series)):
                        y = series[i - window + 1 : i + 1]
                        if len(y) == window:
                            slope = np.polyfit(x, y, 1)[0]
                            result[i] = slope
                    return result
                return series.rolling(window).apply(
                    lambda x: (np.polyfit(np.arange(len(x)), x.values, 1)[0] if len(x) > 1 else 0)
                )

            def Resi(series, window):
                """滚动线性回归残差（实际值 - 拟合值）"""
                if isinstance(series, np.ndarray):
                    result = np.full_like(series, np.nan)
                    x = np.arange(window)
                    for i in range(window - 1, len(series)):
                        y = series[i - window + 1 : i + 1]
                        if len(y) == window:
                            coeffs = np.polyfit(x, y, 1)
                            fitted = np.polyval(coeffs, x)
                            result[i] = y[-1] - fitted[-1]  # 最新值的残差
                    return result
                return series.rolling(window).apply(
                    lambda x: (
                        x.iloc[-1]
                        - np.polyval(np.polyfit(np.arange(len(x)), x.values, 1), len(x) - 1)
                        if len(x) > 1
                        else 0
                    )
                )

            def Rsquare(series, window):
                """滚动线性回归R²"""
                if isinstance(series, np.ndarray):
                    result = np.full_like(series, np.nan)
                    x = np.arange(window)
                    for i in range(window - 1, len(series)):
                        y = series[i - window + 1 : i + 1]
                        if len(y) == window:
                            coeffs = np.polyfit(x, y, 1)
                            fitted = np.polyval(coeffs, x)
                            ss_res = np.sum((y - fitted) ** 2)
                            ss_tot = np.sum((y - np.mean(y)) ** 2)
                            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
                            result[i] = r2
                    return result
                return series.rolling(window).apply(
                    lambda x: (
                        (
                            1
                            - np.sum(
                                (
                                    x.values
                                    - np.polyval(
                                        np.polyfit(np.arange(len(x)), x.values, 1),
                                        np.arange(len(x)),
                                    )
                                )
                                ** 2
                            )
                            / np.sum((x.values - np.mean(x.values)) ** 2)
                            if np.sum((x.values - np.mean(x.values)) ** 2) > 0
                            else 0
                        )
                        if len(x) > 1
                        else 0
                    )
                )

            # 添加到安全字典
            safe_dict.update(
                {
                    "Ref": Ref,
                    "Greater": Greater,
                    "Less": Less,
                    "Sum": Sum,
                    "Mean": Mean,
                    "Std": Std,
                    "Abs": Abs,
                    "Max": Max,
                    "Min": Min,
                    "Log": Log,
                    "Corr": Corr,
                    "Rank": Rank,
                    "Quantile": Quantile,
                    "IdxMax": IdxMax,
                    "IdxMin": IdxMin,
                    "Slope": Slope,
                    "Resi": Resi,
                    "Rsquare": Rsquare,
                }
            )

            # 替换表达式中的变量名（qlib 使用 $close，我们使用 close）
            expr = expr_str.replace(r"$close", "close")
            expr = expr.replace(r"$open", "open")
            expr = expr.replace(r"$high", "high")
            expr = expr.replace(r"$low", "low")
            expr = expr.replace(r"$volume", "volume")
            expr = expr.replace(r"$vwap", "vwap")

            # 计算表达式
            result = eval(expr, safe_dict)

            # 返回最新一行的值
            if isinstance(result, np.ndarray) and len(result) > 0:
                value = result[-1]
                if np.isnan(value) or np.isinf(value):
                    return None
                return float(value)
            elif isinstance(result, (int, float)):
                if np.isnan(result) or np.isinf(result):
                    return None
                return float(result)

            return None

        except Exception as e:
            # 表达式计算失败，返回 None
            return None

    def _value_to_factor_detail(
        self,
        key: str,
        name: str,
        value: float,
        base_key: str = "",
        data_source: str = "",
        raw_data: Optional[dict] = None,
    ) -> Optional[FactorDetail]:
        """
        将因子值转换为 FactorDetail

        统一使用 qlib 库计算因子值，不添加自定义信号生成逻辑。
        只保留基本的因子值转换。

        Args:
            key: 因子 key
            name: 因子名称
            value: 因子值
            base_key: 基础因子 key（未使用，保留以兼容接口）
            data_source: 数据源标识
            raw_data: 原始数据

        Returns:
            FactorDetail 对象
        """
        if value is None or np.isnan(value) or np.isinf(value):
            return None

        # 只保留基本的因子值，不生成自定义信号
        status = f"{value:.4f}"

        return FactorDetail(
            key=key,
            name=name,
            status=status,
            bullish_signals=[],
            bearish_signals=[],
            data_source=data_source,
        )
