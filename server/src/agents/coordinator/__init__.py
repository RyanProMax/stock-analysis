"""
Coordinator - 主协调 Agent

负责协调各子 Agent 并综合分析结果
"""

from .agent import CoordinatorAgent, MultiAgentSystem

__all__ = ["CoordinatorAgent", "MultiAgentSystem"]
