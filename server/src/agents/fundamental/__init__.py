"""
FundamentalAgent - 基本面分析 Agent

负责基本面分析，使用专门的 LLM prompt 生成独立分析结论
"""

from .agent import FundamentalAgent

__all__ = ["FundamentalAgent"]
