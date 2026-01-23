"""
Coordinator - 主协调 Agent 和 MultiAgentSystem

负责协调各子 Agent 并综合分析结果
"""

import asyncio
from typing import Optional, AsyncGenerator, Tuple, Callable, List, Any
from openai.types.chat import ChatCompletionMessageParam

from ..base import BaseAgent, AnalysisState
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
        assert self.llm is not None  # Type narrowing for type checker

        # 标签常量
        THINKING_START = "<thinking>"
        THINKING_END = "</thinking>"
        THINKING_START_LEN = len(THINKING_START)
        THINKING_END_LEN = len(THINKING_END)

        in_thinking = False
        pending_buffer = ""
        max_tokens = get_max_tokens()

        def process_after_end(content: str) -> List[Tuple[str, Optional[str]]]:
            """处理结束标签后的内容，检查嵌套的 thinking 标签"""
            nonlocal in_thinking
            results = []
            if not content:
                return results

            next_thinking = content.find(THINKING_START)
            if next_thinking != -1:
                # 先输出结束标签后到下一个开始标签之间的内容
                if next_thinking > 0:
                    results.append((content[:next_thinking], None))
                # 处理下一个 thinking 块
                next_remaining = content[next_thinking + THINKING_START_LEN :]
                next_end = next_remaining.find(THINKING_END)
                if next_end != -1:
                    if next_remaining[:next_end]:
                        results.append((next_remaining[:next_end], "thinking"))
                    if next_remaining[next_end + THINKING_END_LEN :]:
                        results.append((next_remaining[next_end + THINKING_END_LEN :], None))
                else:
                    if next_remaining:
                        results.append((next_remaining, "thinking"))
                        in_thinking = True
            else:
                results.append((content, None))
            return results

        def is_partial_start_tag(s: str) -> bool:
            """检查是否是部分开始标签"""
            return (
                s.endswith("<")
                or s.endswith("<t")
                or (s.endswith("<th") and THINKING_START not in s)
            )

        def is_partial_end_tag(s: str) -> bool:
            """检查是否是部分结束标签"""
            return (
                s.endswith("<")
                or s.endswith("</")
                or s.endswith("</t")
                or s.endswith("</th")
                or s.endswith("</thi")
                or s.endswith("</thin")
                or s.endswith("</think")
                or s.endswith("</thinking")
            )

        async for chunk in self.llm.chat_completion_stream(
            messages=messages,
            temperature=1.0,
            max_tokens=max_tokens,
        ):
            combined = pending_buffer + chunk
            pending_buffer = ""

            if not in_thinking:
                # 检测 <thinking> 标签开始
                thinking_start = combined.find(THINKING_START)
                if thinking_start != -1:
                    # 输出标签之前的内容
                    if thinking_start > 0:
                        yield (combined[:thinking_start], None)
                    in_thinking = True
                    # 标签之后的内容
                    remaining = combined[thinking_start + THINKING_START_LEN :]
                    # 检查是否在同一 chunk 中有结束标签
                    thinking_end = remaining.find(THINKING_END)
                    if thinking_end != -1:
                        thinking_content = remaining[:thinking_end]
                        if thinking_content:
                            yield (thinking_content, "thinking")
                        in_thinking = False
                        # 处理结束标签后的内容
                        after_end = remaining[thinking_end + THINKING_END_LEN :]
                        for result in process_after_end(after_end):
                            yield result
                    else:
                        # 只有开始标签，输出剩余内容
                        if remaining:
                            yield (remaining, "thinking")
                elif is_partial_start_tag(combined) or (
                    combined.startswith("<") and not combined.startswith(THINKING_START)
                ):
                    # 部分标签或其他标签开头，保存待下次处理
                    pending_buffer = combined
                else:
                    # 正常内容，流式输出
                    yield (combined, None)
            else:
                # 在思考模式中，检测 </thinking> 标签
                thinking_end = combined.find(THINKING_END)
                if thinking_end != -1:
                    # 找到结束标签，输出之前的思考内容
                    before_end = combined[:thinking_end]
                    if before_end:
                        yield (before_end, "thinking")
                    in_thinking = False
                    # 处理结束标签后的内容
                    after_end = combined[thinking_end + THINKING_END_LEN :]
                    for result in process_after_end(after_end):
                        yield result
                elif is_partial_end_tag(combined):
                    # 部分结束标签，保存待下次处理
                    pending_buffer = combined
                else:
                    # 仍在思考模式中，输出思考内容
                    if combined:
                        yield (combined, "thinking")

        # 处理剩余内容
        if pending_buffer:
            yield (pending_buffer, "thinking" if in_thinking else None)

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
        self.fundamental_agent = FundamentalAgent(llm_manager)
        self.technical_agent = TechnicalAgent(llm_manager)
        self.coordinator = CoordinatorAgent(llm_manager)

    async def analyze_stream(
        self,
        symbol: str,
    ) -> AsyncGenerator[
        Tuple[
            str,  # event_type
            AnalysisState,  # state
            Optional[Tuple[str, Optional[str]]],  # stream_chunk (chunk, thinking_type)
            Optional[str],  # message
            Optional[Any],  # data
        ],
        None,
    ]:
        """
        执行完整的 Multi-Agent 分析流程，流式输出进度

        流程：
        1. FundamentalAgent + TechnicalAgent 并行分析（各自负责获取数据，支持流式输出）
        2. 等待两个 Agent 都完成
        3. CoordinatorAgent 综合分析（支持流式输出）

        Yields:
            (event_type, state, stream_chunk, message, data) 元组
            - event_type: 事件类型（如 "fundamental_analyzer:running"）
            - state: 当前分析状态
            - stream_chunk: (chunk, thinking_type) 流式内容元组，如果有
            - message: 进度消息文案
            - data: 可选的附加数据（如因子列表）
        """
        # 初始化状态
        state = AnalysisState(symbol=symbol.upper())

        # 步骤 1: 并行执行基本面和技术面分析（各自负责获取数据）
        progress_queue: asyncio.Queue = asyncio.Queue()
        stream_generators: dict[str, AsyncGenerator] = {}

        async def wrapped_fundamental():
            """执行 fundamental agent 分析，支持流式输出"""
            async for chunk, thinking_type in self.fundamental_agent.analyze_stream(
                state,
                progress_callback=lambda step, status, message, data: progress_queue.put(
                    (step, status, message, data, None)  # 添加 None 作为第5个元素
                ),
            ):
                # 将内容放入队列供前端消费
                await progress_queue.put(
                    (
                        "fundamental_analyzer",
                        "streaming",
                        chunk,
                        None,
                        (chunk, thinking_type),
                    )
                )

        async def wrapped_technical():
            """执行 technical agent 分析，支持流式输出"""
            async for chunk, thinking_type in self.technical_agent.analyze_stream(
                state,
                progress_callback=lambda step, status, message, data: progress_queue.put(
                    (step, status, message, data, None)  # 添加 None 作为第5个元素
                ),
            ):
                # 将内容放入队列供前端消费
                await progress_queue.put(
                    (
                        "technical_analyzer",
                        "streaming",
                        chunk,
                        None,
                        (chunk, thinking_type),
                    )
                )

        # 启动并行任务
        fund_task = asyncio.create_task(wrapped_fundamental())
        tech_task = asyncio.create_task(wrapped_technical())

        # 实时消费进度事件
        completed = 0
        while completed < 2:
            try:
                event = await asyncio.wait_for(progress_queue.get(), timeout=0.01)
                # 事件格式: (step, status, message, data, stream_chunk)
                if len(event) >= 5:
                    step, status, message, data, stream_chunk = event
                else:
                    step, status, message, data = event
                    stream_chunk = None

                # 透传子 Agent 的状态
                yield (f"{step}:{status}", state, stream_chunk, message, data)
                if status in ("completed", "error"):
                    completed += 1
            except asyncio.TimeoutError:
                # 超时，继续循环等待
                continue

        # 等待任务完全完成
        await asyncio.gather(fund_task, tech_task, return_exceptions=True)

        # 检查是否有数据获取错误
        if state.has_error("FundamentalAgent") and state.has_error("TechnicalAgent"):
            # 两个 agent 都失败了
            yield ("error", state, None, "分析失败", None)
            return

        # 步骤 2: 流式输出综合分析的内容
        yield ("coordinator:running", state, None, "正在生成综合报告...", None)

        async for chunk, thinking_type in self.coordinator.synthesize_stream(state):
            yield (f"coordinator:streaming", state, (chunk, thinking_type), None, None)

    async def analyze(
        self,
        symbol: str,
        progress_callback: Optional[Callable] = None,
    ) -> Optional[AnalysisState]:
        """
        执行完整的 Multi-Agent 分析流程（旧版接口，保持兼容）

        Args:
            symbol: 股票代码
            progress_callback: 进度回调函数 callback(step, status, message, data)

        Returns:
            分析状态
        """
        # 使用新的流式接口
        state = None
        async for (
            _event_type,
            event_state,
            _event_stream_chunk,
            _event_message,
            _event_data,
        ) in self.analyze_stream(symbol):
            state = event_state
        return state

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
        full_response = ""
        thinking_response = ""
        state = None

        async for (
            _event_type,
            event_state,
            event_stream_chunk,
            _event_message,
            _event_data,
        ) in self.analyze_stream(symbol):
            state = event_state
            if event_stream_chunk is not None:
                chunk, thinking_type = event_stream_chunk
                if thinking_type == "thinking":
                    thinking_response += chunk
                else:
                    full_response += chunk

        return state, full_response, thinking_response
