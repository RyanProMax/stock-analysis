"""
Coordinator - 主协调 Agent 和 MultiAgentSystem

负责协调各子 Agent 并综合分析结果
"""

import asyncio
from typing import Optional, AsyncGenerator, Tuple, Callable, List, Any, Dict
from openai.types.chat import ChatCompletionMessageParam

from ..base import BaseAgent, AnalysisState, AgentStatus
from ..data import DataAgent
from ..fundamental import FundamentalAgent
from ..technical import TechnicalAgent
from ..llm import LLMManager
from src.env import is_development
from .prompts import (
    COORDINATOR_SYSTEM_MESSAGE,
    build_coordinator_prompt,
)


def get_max_tokens() -> Optional[int]:
    return 500 if is_development() else None


class CoordinatorAgent(BaseAgent):
    """
    主协调 Agent

    职责：
    - 收集所有子 Agent 的分析结果
    - 综合基本面和技术面分析
    - 生成最终投资建议（支持流式输出）
    - 输出思考过程
    """

    def __init__(self, llm_manager: LLMManager):
        super().__init__(llm_manager=llm_manager)
        self.set_name("CoordinatorAgent")

    async def analyze(
        self, state: AnalysisState, progress_callback: Optional[Callable] = None
    ) -> AnalysisState:
        """
        执行综合分析（实现 BaseAgent 的抽象方法）

        Args:
            state: 包含所有子 Agent 分析结果的状态
            progress_callback: 进度回调函数

        Returns:
            更新后的状态（包含综合分析结果）
        """
        self._start_timing()

        if progress_callback:
            await progress_callback("正在综合分析...")

        # 调用 synthesize 获取完整分析结果
        full_analysis, thinking = await self.synthesize(state)
        state.coordinator_analysis = full_analysis
        state.thinking_process = thinking

        execution_time = self._end_timing()
        state.set_execution_time(self.get_name(), execution_time)

        return state

    async def synthesize_stream(
        self, state: AnalysisState
    ) -> AsyncGenerator[Tuple[str, Optional[str]], None]:
        """
        综合分析并流式输出结果

        Args:
            state: 包含所有子 Agent 分析结果的状态

        Yields:
            (content, thinking_type) 元组
            - content: LLM 生成的文本片段
            - thinking_type: None 表示正常内容, "thinking" 表示思考过程
        """
        # 检查数据完整性
        if not state.fundamental_analysis:
            yield ("基本面分析缺失，无法进行综合分析。", None)
            return
        if not state.technical_analysis:
            yield ("技术面分析缺失，无法进行综合分析。", None)
            return

        # 构建综合分析 prompt
        user_prompt = build_coordinator_prompt(
            symbol=state.symbol,
            stock_name=state.stock_name,
            industry=state.industry,
            fundamental_analysis=state.fundamental_analysis,
            technical_analysis=state.technical_analysis,
        )

        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": COORDINATOR_SYSTEM_MESSAGE},
            {"role": "user", "content": user_prompt},
        ]

        # 流式输出 LLM 响应
        if not self.llm or not self.llm.is_available:
            yield ("LLM 未配置，无法生成综合分析。", None)
            return

        thinking_buffer = ""
        content_buffer = ""
        in_thinking = False
        max_tokens = get_max_tokens()

        async for chunk in self.llm.chat_completion_stream(
            messages=messages,
            temperature=1.0,
            max_tokens=max_tokens,
        ):
            # 检测 thinking 标签
            if "<thinking>" in chunk:
                in_thinking = True
                # 分割 chunk，处理 thinking 标签前后的内容
                parts = chunk.split("<thinking>", 1)
                if parts[0]:
                    yield (parts[0], None)
                if len(parts) > 1:
                    thinking_buffer += parts[1]
                continue

            if "</thinking>" in chunk:
                in_thinking = False
                # 分割 chunk，完成 thinking 并开始内容
                parts = chunk.split("</thinking>", 1)
                thinking_buffer += parts[0]
                # 输出完整的思考过程
                if thinking_buffer.strip():
                    yield (thinking_buffer.strip(), "thinking")
                thinking_buffer = ""
                if len(parts) > 1 and parts[1]:
                    yield (parts[1], None)
                continue

            if in_thinking:
                thinking_buffer += chunk
            else:
                yield (chunk, None)

    async def synthesize(self, state: AnalysisState) -> Tuple[str, str]:
        """
        综合分析（非流式，返回完整结果）

        Args:
            state: 包含所有子 Agent 分析结果的状态

        Returns:
            (完整综合分析文本, 思考过程)
        """
        full_response = ""
        thinking_response = ""

        async for chunk, thinking_type in self.synthesize_stream(state):
            if thinking_type == "thinking":
                thinking_response += chunk
            else:
                full_response += chunk

        return full_response, thinking_response


class MultiAgentSystem:
    """
    Multi-Agent 系统

    职责：
    - 管理所有 Agent 实例
    - 协调 Agent 执行流程
    - 提供统一的接口给 Controller 使用
    - 跟踪每个 Agent 的执行时间
    """

    def __init__(self, llm_manager: LLMManager):
        """
        初始化 Multi-Agent 系统

        Args:
            llm_manager: LLM 管理器
        """
        self.llm_manager = llm_manager
        self.data_agent = DataAgent()
        self.fundamental_agent = FundamentalAgent(llm_manager)
        self.technical_agent = TechnicalAgent(llm_manager)
        self.coordinator = CoordinatorAgent(llm_manager)

    async def analyze(
        self,
        symbol: str,
        progress_callback: Optional[Callable] = None,
    ) -> Tuple[AnalysisState, AsyncGenerator[Tuple[str, Optional[str]], None]]:
        """
        执行完整的 Multi-Agent 分析流程

        流程：
        1. DataAgent 获取数据
        2. FundamentalAgent + TechnicalAgent 并行分析
        3. CoordinatorAgent 综合分析（返回流式生成器）

        Args:
            symbol: 股票代码
            progress_callback: 进度回调函数 callback(step, status, message, data)

        Returns:
            (分析状态, 流式输出生成器)
        """
        # 初始化状态
        state = AnalysisState(symbol=symbol.upper())

        # 步骤 1: 数据获取
        if progress_callback:
            await progress_callback("data_agent", "running", f"正在获取 {symbol} 数据...")

        state = await self.data_agent.analyze(state)

        if state.has_error("DataAgent"):
            if progress_callback:
                await progress_callback(
                    "data_agent",
                    "error",
                    state.errors["DataAgent"],
                    {"execution_time": state.execution_times.get("DataAgent", 0)},
                )
            return state, self._error_stream(state.errors["DataAgent"])

        if progress_callback:
            await progress_callback(
                "data_agent",
                "success",
                "数据获取完成",
                {"execution_time": state.execution_times.get("DataAgent", 0)},
            )

        # 步骤 2: 并行执行基本面和技术面分析
        if progress_callback:
            await progress_callback("parallel_analysis", "running", "正在并行分析...")

        await asyncio.gather(
            self.fundamental_agent.analyze(state),
            self.technical_agent.analyze(state),
        )

        # 检查分析结果
        if state.has_error("FundamentalAgent"):
            if progress_callback:
                await progress_callback(
                    "fundamental_agent",
                    "error",
                    state.errors["FundamentalAgent"],
                    {"execution_time": state.execution_times.get("FundamentalAgent", 0)},
                )
        else:
            if progress_callback:
                await progress_callback(
                    "fundamental_agent",
                    "success",
                    "基本面分析完成",
                    {"execution_time": state.execution_times.get("FundamentalAgent", 0)},
                )

        if state.has_error("TechnicalAgent"):
            if progress_callback:
                await progress_callback(
                    "technical_agent",
                    "error",
                    state.errors["TechnicalAgent"],
                    {"execution_time": state.execution_times.get("TechnicalAgent", 0)},
                )
        else:
            if progress_callback:
                await progress_callback(
                    "technical_agent",
                    "success",
                    "技术面分析完成",
                    {"execution_time": state.execution_times.get("TechnicalAgent", 0)},
                )

        if progress_callback:
            await progress_callback("parallel_analysis", "success", "子分析完成")

        # 步骤 3: 返回综合分析的流式生成器
        return state, self.coordinator.synthesize_stream(state)

    async def analyze_full(
        self,
        symbol: str,
        progress_callback: Optional[Callable] = None,
    ) -> Tuple[AnalysisState, str, str]:
        """
        执行完整分析并返回完整结果（非流式）

        Args:
            symbol: 股票代码
            progress_callback: 进度回调函数

        Returns:
            (分析状态, 完整综合分析文本, 思考过程)
        """
        state, stream_gen = await self.analyze(symbol, progress_callback)

        full_response = ""
        thinking_response = ""

        async for chunk, thinking_type in stream_gen:
            if thinking_type == "thinking":
                thinking_response += chunk
            else:
                full_response += chunk

        return state, full_response, thinking_response

    def _error_stream(self, error_msg: str) -> AsyncGenerator[Tuple[str, Optional[str]], None]:
        """生成错误消息流"""

        async def gen():
            yield (f"分析失败: {error_msg}", None)

        return gen()
