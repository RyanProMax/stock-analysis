from abc import ABC, abstractmethod
from typing import List
import pandas as pd
from stockstats import StockDataFrame

from ..model import FactorDetail


class BaseFactor(ABC):
    """
    因子基类

    职责：
    1. 定义统一的因子计算接口规范
    2. 确保所有因子实现类的一致性
    3. 提供通用的工具方法

    接口规范：
    - 输入：StockDataFrame（包含技术指标）、DataFrame（原始数据）、其他参数
    - 输出：FactorDetail（因子详情）
    """

    def __init__(self, stock: StockDataFrame, raw_df: pd.DataFrame):
        """
        初始化因子

        Args:
            stock: StockDataFrame 对象，包含计算好的技术指标
            raw_df: 原始行情数据 DataFrame
        """
        if stock is None:
            raise ValueError("StockDataFrame cannot be None")
        if raw_df is None or raw_df.empty:
            raise ValueError("DataFrame cannot be None or empty")

        self.stock = stock
        self.raw_df = raw_df

    @abstractmethod
    def calculate(self, **kwargs) -> FactorDetail:
        """
        计算因子（抽象方法，子类必须实现）

        Args:
            **kwargs: 额外的参数，如 financial_data, fg_index 等

        Returns:
            FactorDetail: 因子详情对象
        """
        pass

    @staticmethod
    def _create_signal(signal_type: str, message: str) -> dict:
        """
        创建信号字典

        Args:
            signal_type: 信号类型，"fundamental"（基本面）或 "technical"（技术面）
            message: 信号内容

        Returns:
            包含 type 和 message 的字典
        """
        return {"type": signal_type, "message": message}

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


class FactorLibrary(ABC):
    """
    因子库基类

    职责：
    1. 定义因子库的统一接口
    2. 管理一组相关因子的计算
    """

    @abstractmethod
    def get_factors(
        self, stock: StockDataFrame, raw_df: pd.DataFrame, **kwargs
    ) -> List[FactorDetail]:
        """
        获取因子库中的所有因子

        Args:
            stock: StockDataFrame 对象
            raw_df: 原始行情数据 DataFrame
            **kwargs: 额外的参数

        Returns:
            List[FactorDetail]: 因子详情列表
        """
        pass
