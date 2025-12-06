from abc import ABC, abstractmethod
import pandas as pd

from ..model import AnalysisReport


class BaseStockAnalyzer(ABC):
    """
    股票分析策略基类

    职责：
    1. 定义统一的输入输出接口规范
    2. 确保所有策略实现类的一致性
    3. 提供通用的工具方法

    接口规范：
    - 输入：DataFrame（行情数据）、symbol（股票代码）、stock_name（股票名称）
    - 输出：AnalysisReport（分析报告）或 None（分析失败）
    """

    def __init__(self, df: pd.DataFrame, symbol: str, stock_name: str):
        """
        初始化分析器

        Args:
            df: 股票行情数据 DataFrame，需包含 open, close, high, low, volume 等列
            symbol: 股票代码（如 'NVDA', '600519'）
            stock_name: 股票名称
        """
        if df is None or df.empty:
            raise ValueError("DataFrame cannot be None or empty")
        if not symbol or not symbol.strip():
            raise ValueError("Symbol cannot be empty")

        self.raw_df = df.copy()
        self.symbol = symbol.strip().upper()
        self.stock_name = stock_name or symbol

    @abstractmethod
    def analyze(self) -> AnalysisReport | None:
        """
        执行股票分析（抽象方法，子类必须实现）

        Returns:
            AnalysisReport: 分析报告对象，包含因子详情和信号等信息
            None: 分析失败（如数据不足、价格异常等）
        """
        pass

    @staticmethod
    def _clamp_ratio(value: float) -> float:
        """
        将数值限制在 0-1 范围内

        Args:
            value: 原始数值

        Returns:
            限制后的数值（0.0 <= value <= 1.0）
        """
        return max(0.0, min(1.0, value))
