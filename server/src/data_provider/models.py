"""
数据模型定义

定义统一的日线数据结构。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Any
import pandas as pd


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    安全转换为 float，处理 None 和 NaN

    Args:
        value: 待转换的值
        default: 默认值

    Returns:
        转换后的 float 值
    """
    if value is None or pd.isna(value):
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_optional_float(value: Any) -> Optional[float]:
    """
    安全转换为 Optional[float]，返回 None 如果值为空

    Args:
        value: 待转换的值

    Returns:
        转换后的 float 值或 None
    """
    if value is None or pd.isna(value):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


@dataclass
class DailyData:
    """
    统一日线数据结构

    必填字段：date, open, high, low, close, volume
    可选字段：amount, pct_chg
    """

    # 必填字段
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str  # 数据来源

    # 可选字段
    amount: Optional[float] = None
    pct_chg: Optional[float] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "date": self.date.isoformat() if self.date else None,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "amount": self.amount,
            "pct_chg": self.pct_chg,
            "source": self.source,
        }

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, source: str) -> List["DailyData"]:
        """
        从 DataFrame 创建 DailyData 列表

        Args:
            df: 标准化后的 DataFrame（列名已标准化）
            source: 数据源名称

        Returns:
            DailyData 列表
        """
        records = []

        for _, row in df.iterrows():
            # 提取日期
            date_val: Optional[datetime] = None
            raw_date = row.get("date")
            if raw_date is not None and pd.notna(raw_date):
                if isinstance(raw_date, str):
                    date_val = pd.to_datetime(raw_date).to_pydatetime()
                elif isinstance(raw_date, pd.Timestamp):
                    date_val = raw_date.to_pydatetime()
                elif isinstance(raw_date, datetime):
                    date_val = raw_date

            record = cls(
                date=date_val,  # type: ignore
                open=safe_float(row.get("open")),
                high=safe_float(row.get("high")),
                low=safe_float(row.get("low")),
                close=safe_float(row.get("close")),
                volume=safe_float(row.get("volume")),
                source=source,
                amount=safe_optional_float(row.get("amount")),
                pct_chg=safe_optional_float(row.get("pct_chg")),
            )
            records.append(record)

        return records

    def to_dataframe(self) -> pd.DataFrame:
        """转换为 DataFrame（单条记录）"""
        return pd.DataFrame([self.to_dict()])


@dataclass
class DailyDataCollection:
    """
    日线数据集合

    包含一只股票的完整日线数据
    """

    symbol: str
    name: str
    data: List[DailyData]
    source: str

    @property
    def count(self) -> int:
        """数据条数"""
        return len(self.data)

    @property
    def latest(self) -> Optional[DailyData]:
        """最新一条数据"""
        return self.data[-1] if self.data else None

    @property
    def first(self) -> Optional[DailyData]:
        """最早一条数据"""
        return self.data[0] if self.data else None

    def to_dataframe(self) -> pd.DataFrame:
        """转换为 DataFrame"""
        if not self.data:
            return pd.DataFrame()

        records = [d.to_dict() for d in self.data]
        df = pd.DataFrame(records)
        df["symbol"] = self.symbol
        df["name"] = self.name
        return df

    @classmethod
    def from_dataframe(
        cls, df: pd.DataFrame, symbol: str, name: str, source: str
    ) -> "DailyDataCollection":
        """
        从 DataFrame 创建集合

        Args:
            df: 标准化后的 DataFrame
            symbol: 股票代码
            name: 股票名称
            source: 数据源

        Returns:
            DailyDataCollection
        """
        data = DailyData.from_dataframe(df, source)
        return cls(symbol=symbol, name=name, data=data, source=source)
