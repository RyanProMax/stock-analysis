"""
DataAgent - 数据获取 Agent

负责获取股票数据，不使用 LLM，直接调用 stock_service
"""

from .agent import DataAgent

__all__ = ["DataAgent"]
