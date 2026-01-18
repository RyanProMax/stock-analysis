"""
Agent Base Module - 统一的 Agent 基类和状态管理
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Any, Dict, List, AsyncGenerator, Callable
from enum import Enum
import pandas as pd

from ..core import FactorAnalysis


class AgentStatus(Enum):
    """Agent 执行状态"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class AnalysisState:
    """分析状态 - 在各 Agent 之间传递的共享状态"""

    # 股票基本信息
    symbol: str
    stock_name: str = ""
    industry: str = ""
    price: float = 0.0

    # 数据层（由分析 Agent 填充）
    price_data: Optional[pd.DataFrame] = None
    financial_data: Optional[dict] = None
    stock_data: Optional[Any] = None

    # 基本面分析结果（由 FundamentalAgent 填充）
    fundamental: Optional[FactorAnalysis] = None
    fundamental_analysis: str = ""

    # 技术面分析结果（由 TechnicalAgent 填充）
    technical: Optional[FactorAnalysis] = None
    technical_analysis: str = ""

    # 综合分析结果（由 Coordinator 填充）
    coordinator_analysis: str = ""
    thinking_process: str = ""

    # 数据获取标记（防止重复获取）
    _data_fetched: bool = False

    # 错误跟踪
    errors: Dict[str, str] = field(default_factory=dict)

    # 执行时间跟踪
    execution_times: Dict[str, float] = field(default_factory=dict)

    def has_error(self, agent_name: str) -> bool:
        """检查指定 agent 是否有错误"""
        return agent_name in self.errors

    def set_error(self, agent_name: str, error_msg: str):
        """设置 agent 错误"""
        self.errors[agent_name] = error_msg

    def is_ready(self) -> bool:
        """检查状态是否准备好进行协调分析"""
        return bool(
            self.price_data is not None and self.fundamental_analysis and self.technical_analysis
        )

    def set_execution_time(self, agent_name: str, duration: float):
        """记录 agent 执行时间"""
        self.execution_times[agent_name] = duration


@dataclass
class AgentResult:
    """Agent 执行结果"""

    agent_name: str
    status: AgentStatus
    data: Optional[Any] = None
    message: str = ""
    error: Optional[str] = None
    execution_time: float = 0.0

    @classmethod
    def success_result(
        cls,
        agent_name: str,
        data: Any = None,
        message: str = "",
        execution_time: float = 0.0,
    ):
        return cls(
            agent_name=agent_name,
            status=AgentStatus.SUCCESS,
            data=data,
            message=message,
            execution_time=execution_time,
        )

    @classmethod
    def error_result(cls, agent_name: str, error: str, execution_time: float = 0.0):
        return cls(
            agent_name=agent_name,
            status=AgentStatus.ERROR,
            error=error,
            execution_time=execution_time,
        )

    @classmethod
    def running_result(cls, agent_name: str, message: str = ""):
        return cls(agent_name=agent_name, status=AgentStatus.RUNNING, message=message)


class BaseAgent(ABC):
    """
    Agent 基类

    所有子 Agent 必须继承此类并实现 analyze 方法。
    每个 Agent 负责一个特定的分析维度，接收 AnalysisState，
    执行分析后更新状态并返回。
    """

    def __init__(self, llm_manager: Optional[Any] = None):
        """
        初始化 Agent

        Args:
            llm_manager: LLM 管理器，用于需要 LLM 的 Agent
        """
        self.llm = llm_manager
        self._name = self.__class__.__name__
        self._start_time: Optional[float] = None

    @abstractmethod
    async def analyze(
        self, state: AnalysisState, progress_callback: Optional[Callable] = None
    ) -> AnalysisState:
        """
        执行分析并更新状态

        Args:
            state: 当前分析状态
            progress_callback: 进度回调函数 callback(message, data)

        Returns:
            更新后的分析状态
        """
        pass

    def get_name(self) -> str:
        """获取 Agent 名称"""
        return self._name

    def set_name(self, name: str):
        """设置 Agent 名称"""
        self._name = name

    def _start_timing(self):
        """开始计时"""
        self._start_time = time.time()

    def _end_timing(self) -> float:
        """结束计时并返回耗时（秒）"""
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time

    async def _call_llm(
        self,
        messages: List[Any],
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        调用 LLM 生成回复

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            LLM 的完整回复
        """
        if not self.llm or not self.llm.is_available:
            return "LLM 未配置"

        assert self.llm is not None  # Type narrowing for type checker

        full_response = ""
        async for chunk in self.llm.chat_completion_stream(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            full_response += chunk
        return full_response

    async def _call_llm_stream(
        self,
        messages: List[Any],
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """
        调用 LLM 并流式输出

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大 token 数

        Yields:
            LLM 生成的文本片段
        """
        if not self.llm or not self.llm.is_available:
            yield "LLM 未配置"
            return

        assert self.llm is not None  # Type narrowing for type checker

        async for chunk in self.llm.chat_completion_stream(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            yield chunk
