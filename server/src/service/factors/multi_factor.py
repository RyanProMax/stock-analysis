from stockstats import StockDataFrame
import pandas as pd

from ..model import AnalysisReport, FearGreed
from ..data_loader import DataLoader
from .base import BaseFactor
from .technical_factors import TechnicalFactorLibrary
from .fundamental_factors import FundamentalFactorLibrary
from .qlib_158_factors import Qlib158FactorLibrary


class MultiFactorAnalyzer:
    """
    多因子股票分析器

    核心设计理念：
    1. 加载各个因子库（技术面、基本面、qlib158等）
    2. 统一输出因子列表
    3. 每个因子库独立管理自己的因子计算逻辑

    因子库：
    - TechnicalFactorLibrary: 技术面因子库（MA、EMA、MACD、RSI等）
    - FundamentalFactorLibrary: 基本面因子库（营收增长率、PE、PB等）
    - Qlib158FactorLibrary: Qlib 158 经典因子库
    """

    # 需要计算的技术指标列表（按因子分类）
    INDICATORS_TO_CALCULATE = [
        # 趋势指标
        "macd",  # MACD 主线
        "macdh",  # MACD 柱线（用于趋势判断）
        "macds",  # MACD 信号线
        "close_12_ema",  # 12日指数均线
        "close_26_ema",  # 26日指数均线
        "close_5_sma",  # 5日简单均线
        "close_10_sma",  # 10日简单均线
        "close_20_sma",  # 20日简单均线
        "close_60_sma",  # 60日简单均线
        # 动量指标
        "rsi_14",  # 14日 RSI 相对强弱指标
        "kdjk",  # KDJ 指标 K 值
        "kdjd",  # KDJ 指标 D 值
        "kdjj",  # KDJ 指标 J 值
        "wr_14",  # 14日威廉指标
        # 波动率指标
        "boll",  # 布林带中轨
        "boll_ub",  # 布林带上轨
        "boll_lb",  # 布林带下轨
        "atr",  # 真实波动幅度（用于止损计算）
        # 量能指标
        "vr",  # 成交量比率
        "volume",  # 成交量
    ]

    def __init__(self, df: pd.DataFrame, symbol: str, stock_name: str):
        """
        初始化多因子分析器

        Args:
            df: 股票行情数据 DataFrame
            symbol: 股票代码
            stock_name: 股票名称
        """
        if df is None or df.empty:
            raise ValueError("DataFrame cannot be None or empty")
        if not symbol or not symbol.strip():
            raise ValueError("Symbol cannot be empty")

        self.raw_df = df.copy()
        self.symbol = symbol.strip().upper()
        self.stock_name = stock_name or symbol

        # 初始化技术指标计算引擎
        self.stock = StockDataFrame.retype(self.raw_df.copy())

        # 计算所需的技术指标
        for indicator in self.INDICATORS_TO_CALCULATE:
            self.stock.get(indicator)

        # 初始化因子库
        self.technical_library = TechnicalFactorLibrary()
        self.fundamental_library = FundamentalFactorLibrary()
        self.qlib158_library = Qlib158FactorLibrary()

    def _calculate_fear_greed(self, row, close) -> tuple[float, str]:
        """
        计算个股贪恐指数（Fear & Greed Index）

        基于 RSI、布林带 %B、威廉指标 WR 合成
        """
        try:
            # 1. RSI (0-100)
            rsi = float(row.get("rsi_14", 50) or 50)

            # 2. 布林带 %B (0-100)
            lb = float(row.get("boll_lb", close * 0.9) or close * 0.9)
            ub = float(row.get("boll_ub", close * 1.1) or close * 1.1)
            if ub != lb:
                pct_b = (close - lb) / (ub - lb) * 100
            else:
                pct_b = 50
            pct_b = max(0, min(100, pct_b))  # 截断极端值

            # 3. 威廉指标 WR (-100 到 0) -> 映射为 (0 到 100)
            wr = float(row.get("wr_14", -50) or -50)
            wr_score = wr + 100

            # 合成指数
            fg_index = (rsi * 0.4) + (pct_b * 0.4) + (wr_score * 0.2)

            # 生成标签
            if fg_index <= 20:
                label = "🥶 极度恐慌"
            elif fg_index <= 40:
                label = "😨 恐慌"
            elif fg_index <= 60:
                label = "😐 中性"
            elif fg_index <= 80:
                label = "🤤 贪婪"
            else:
                label = "🔥 极度贪婪"

            return fg_index, label
        except Exception as e:
            # 如果计算失败，返回默认值
            print(f"⚠️ 计算贪恐指数失败: {e}")
            return 50.0, "😐 中性"

    def analyze(self) -> AnalysisReport | None:
        """
        执行完整的股票技术分析流程

        核心流程：
        1. 提取最新行情数据和技术指标
        2. 获取财务数据（营收、负债、市盈率等）
        3. 计算贪恐指数（用于波动率因子）
        4. 从各个因子库加载因子
        5. 汇总所有因子
        """
        last_row = self.stock.iloc[-1]
        prev_row = self.stock.iloc[-2] if len(self.stock) > 1 else last_row

        close = float(last_row.get("close", 0.0))
        if close == 0.0:
            return None

        # 计算贪恐指数（用于波动率因子）
        fg_index, fg_label = self._calculate_fear_greed(last_row, close)

        # 计算成交量均线（用于量能因子）
        volume_series = (
            self.raw_df["volume"]
            if "volume" in self.raw_df.columns
            else pd.Series([last_row.get("volume", 0)])
        )
        # 使用 ffill() 替代已弃用的 fillna(method="ffill")
        volume_series = volume_series.ffill().fillna(0)
        volume_ma5 = float(volume_series.tail(5).mean())
        volume_ma20 = (
            float(volume_series.tail(20).mean()) if len(volume_series) >= 20 else volume_ma5
        )

        # --- 获取财务数据（基本面因子）---
        financial_data = None
        try:
            financial_data = DataLoader.get_financial_data(self.symbol)
        except Exception as e:
            import traceback

            print(f"⚠️ 获取财务数据失败: {e}")
            print("财务数据获取错误堆栈:")
            traceback.print_exc()

        # --- 从各个因子库加载因子 ---
        technical_factors = []
        fundamental_factors = []
        qlib_factors = []

        # 1. 技术面因子库
        try:
            technical_factors = self.technical_library.get_factors(
                self.stock,
                self.raw_df,
                fg_index=fg_index,
                volume_ma5=volume_ma5,
                volume_ma20=volume_ma20,
            )
        except Exception as e:
            import traceback

            print(f"⚠️ 计算技术面因子失败: {e}")
            traceback.print_exc()

        # 2. 基本面因子库
        try:
            fundamental_factors = self.fundamental_library.get_factors(
                self.stock,
                self.raw_df,
                financial_data=financial_data,
            )
        except Exception as e:
            import traceback

            print(f"⚠️ 计算基本面因子失败: {e}")
            traceback.print_exc()

        # 3. Qlib 158 因子库
        try:
            qlib_factors = self.qlib158_library.get_factors(
                self.stock,
                self.raw_df,
                symbol=self.symbol,
            )
        except Exception as e:
            import traceback

            print(f"⚠️ 计算 Qlib 158 因子失败: {e}")
            traceback.print_exc()

        # 创建贪恐指数对象
        fear_greed = FearGreed(index=fg_index, label=fg_label)

        report = AnalysisReport(
            symbol=self.symbol,
            stock_name=self.stock_name,
            price=close,
            technical_factors=technical_factors,
            fundamental_factors=fundamental_factors,
            qlib_factors=qlib_factors,
            fear_greed=fear_greed,
        )

        return report
