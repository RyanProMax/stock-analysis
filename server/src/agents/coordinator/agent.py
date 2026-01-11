"""
Coordinator - 主协调 Agent 和 MultiAgentSystem

负责协调各子 Agent 并综合分析结果
"""

import asyncio
from typing import Optional, AsyncGenerator, Tuple, Callable, List
from openai.types.chat import ChatCompletionMessageParam

from ..base import BaseAgent, AnalysisState
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

        assert self.llm is not None  # Type narrowing for type checker

        thinking_buffer = ""
        in_thinking = False
        # 用于处理跨 chunk 的标签检测
        pending_buffer = ""
        max_tokens = get_max_tokens()

        async for chunk in self.llm.chat_completion_stream(
            messages=messages,
            temperature=1.0,
            max_tokens=max_tokens,
        ):
            # 将待处理内容和当前 chunk 合并
            combined = pending_buffer + chunk
            pending_buffer = ""

            if not in_thinking:
                # 检测 <thinking> 标签开始
                thinking_start = combined.find("<thinking>")
                if thinking_start != -1:
                    # 输出标签之前的内容
                    if thinking_start > 0:
                        yield (combined[:thinking_start], None)
                    # 进入思考模式
                    in_thinking = True
                    # 标签之后的内容可能是思考内容
                    remaining = combined[thinking_start + len("<thinking>") :]
                    # 检查是否在同一 chunk 中有结束标签
                    thinking_end = remaining.find("</thinking>")
                    if thinking_end != -1:
                        # 同一 chunk 中有开始和结束标签
                        thinking_content = remaining[:thinking_end]
                        if thinking_content.strip():
                            yield (thinking_content, "thinking")
                        # 退出思考模式
                        in_thinking = False
                        # 结束标签后的内容
                        pending_buffer = remaining[thinking_end + len("</thinking>") :]
                    else:
                        # 只有开始标签，保存剩余内容
                        thinking_buffer = remaining
                else:
                    # 检测部分标签（可能跨 chunk）
                    if (
                        combined.endswith("<")
                        or combined.endswith("<t")
                        or combined.endswith("<th")
                        or combined.endswith("<thi")
                        or combined.endswith("<thin")
                        or combined.endswith("<think")
                        or combined.endswith("<thinki")
                        or combined.endswith("<thinkin")
                    ):
                        # 可能是 <thinking> 标签的开始，保存待下次处理
                        pending_buffer = combined
                    elif combined.startswith("<") and not combined.startswith("<thinking>"):
                        # 检查是否是标签的一部分
                        pending_buffer = combined
                    else:
                        # 正常内容
                        yield (combined, None)
            else:
                # 在思考模式中，检测 </thinking> 标签
                thinking_end = combined.find("</thinking>")
                if thinking_end != -1:
                    # 找到结束标签
                    thinking_buffer += combined[:thinking_end]
                    if thinking_buffer.strip():
                        yield (thinking_buffer.strip(), "thinking")
                    thinking_buffer = ""
                    in_thinking = False
                    # 结束标签后的内容
                    pending_buffer = combined[thinking_end + len("</thinking>") :]
                else:
                    # 仍在思考模式中
                    thinking_buffer += combined

        # 处理剩余内容
        if in_thinking and thinking_buffer.strip():
            yield (thinking_buffer.strip(), "thinking")
        if pending_buffer and not in_thinking:
            yield (pending_buffer, None)

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

    async def analyze_stream(
        self,
        symbol: str,
    ) -> AsyncGenerator[
        Tuple[
            str,
            AnalysisState,
            Optional[AsyncGenerator[Tuple[str, Optional[str]], None]],
            Optional[str],
        ],
        None,
    ]:
        """
        执行完整的 Multi-Agent 分析流程，流式输出进度

        流程：
        1. DataAgent 获取数据
        2. FundamentalAgent + TechnicalAgent 并行分析
        3. CoordinatorAgent 综合分析（返回流式生成器）

        Yields:
            (event_type, state, stream_gen, message) 元组
            - event_type: 事件类型（如 "data_agent:running"）
            - state: 当前分析状态
            - stream_gen: 综合分析的流式生成器（仅在 coordinator 时有值）
            - message: 进度消息文案
        """
        # 初始化状态
        state = AnalysisState(symbol=symbol.upper())

        # 步骤 1: 数据获取
        yield ("progress", state, None, None)
        yield ("data_agent:running", state, None, f"正在获取 {symbol} 数据...")

        state = await self.data_agent.analyze(state)

        if state.has_error("DataAgent"):
            yield (
                "data_agent:error",
                state,
                None,
                state.errors.get("DataAgent", "数据获取失败"),
            )
            yield ("error", state, None, state.errors.get("DataAgent", "数据获取失败"))
            return

        yield ("data_agent:success", state, None, "数据获取完成")

        # 步骤 2: 并行执行基本面和技术面分析（透传子 Agent 状态）
        progress_queue: asyncio.Queue = asyncio.Queue()

        async def wrapped_fundamental():
            """透传 fundamental agent 的状态回调"""
            await self.fundamental_agent.analyze(
                state,
                progress_callback=lambda step, status, message, data: progress_queue.put(
                    (step, status, message)
                ),
            )

        async def wrapped_technical():
            """透传 technical agent 的状态回调"""
            await self.technical_agent.analyze(
                state,
                progress_callback=lambda step, status, message, data: progress_queue.put(
                    (step, status, message)
                ),
            )

        # 启动并行任务
        fund_task = asyncio.create_task(wrapped_fundamental())
        tech_task = asyncio.create_task(wrapped_technical())

        # 实时消费进度事件
        completed = 0
        while completed < 2:
            try:
                event = await asyncio.wait_for(progress_queue.get(), timeout=0.01)
                step, status, message = event
                # 透传子 Agent 的状态
                yield (f"{step}:{status}", state, None, message)
                if status in ("success", "error"):
                    completed += 1
            except asyncio.TimeoutError:
                # 检查任务是否完成
                if fund_task.done():
                    completed += 1
                if tech_task.done():
                    completed += 1
                if completed >= 2:
                    break
                continue

        # 等待任务完全完成
        await asyncio.gather(fund_task, tech_task, return_exceptions=True)

        # 步骤 3: 返回综合分析的流式生成器
        yield (
            "coordinator:running",
            state,
            self.coordinator.synthesize_stream(state),
            "正在生成综合报告...",
        )

    async def analyze(
        self,
        symbol: str,
        progress_callback: Optional[Callable] = None,
    ) -> Tuple[
        Optional[AnalysisState],
        Optional[AsyncGenerator[Tuple[str, Optional[str]], None]],
    ]:
        """
        执行完整的 Multi-Agent 分析流程（旧版接口，保持兼容）

        Args:
            symbol: 股票代码
            progress_callback: 进度回调函数 callback(step, status, message, data)

        Returns:
            (分析状态, 流式输出生成器)
        """
        # 使用新的流式接口
        state = None
        stream_gen = None
        async for event_type, event_state, event_stream_gen, _ in self.analyze_stream(symbol):
            state = event_state
            if event_stream_gen is not None:
                stream_gen = event_stream_gen
        return state, stream_gen

    async def analyze_full(
        self,
        symbol: str,
        progress_callback: Optional[Callable] = None,
    ) -> Tuple[Optional[AnalysisState], str, str]:
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

        if stream_gen is not None:
            async for chunk, thinking_type in stream_gen:
                if thinking_type == "thinking":
                    thinking_response += chunk
                else:
                    full_response += chunk

        return state, full_response, thinking_response
