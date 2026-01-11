"""
Multi-Agent 系统 - 股票分析 Agent 框架

提供模块化的 Agent 架构，每个 Agent 负责特定的分析维度。
"""

from .base import BaseAgent, AnalysisState, AgentStatus, AgentResult
from .llm import LLMManager, LLMProvider
from .coordinator import CoordinatorAgent, MultiAgentSystem
from .fundamental import FundamentalAgent
from .technical import TechnicalAgent

__all__ = [
    "BaseAgent",
    "AnalysisState",
    "AgentStatus",
    "AgentResult",
    "LLMManager",
    "LLMProvider",
    "CoordinatorAgent",
    "MultiAgentSystem",
    "FundamentalAgent",
    "TechnicalAgent",
]
