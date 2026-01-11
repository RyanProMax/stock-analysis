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
        if not self.llm or not self.llm.is_available:
            yield ("LLM 未配置，无法生成综合分析。", None)
            return

        assert self.llm is not None  # Type narrowing for type checker

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
                    # 标签之后的内容
                    remaining = combined[thinking_start + len("<thinking>") :]
                    # 检查是否在同一 chunk 中有结束标签
                    thinking_end = remaining.find("</thinking>")
                    if thinking_end != -1:
                        # 同一 chunk 中有开始和结束标签
                        thinking_content = remaining[:thinking_end]
                        if thinking_content:
                            yield (thinking_content, "thinking")
                        # 退出思考模式
                        in_thinking = False
                        # 结束标签后的内容
                        after_end = remaining[thinking_end + len("</thinking>") :]
                        if after_end:
                            # 检查是否还有嵌套的 thinking 标签
                            next_thinking = after_end.find("<thinking>")
                            if next_thinking != -1:
                                # 先输出结束标签后到下一个开始标签之间的内容
                                if next_thinking > 0:
                                    yield (after_end[:next_thinking], None)
                                # 处理下一个 thinking 块
                                next_remaining = after_end[next_thinking + len("<thinking>") :]
                                next_end = next_remaining.find("</thinking>")
                                if next_end != -1:
                                    if next_remaining[:next_end]:
                                        yield (next_remaining[:next_end], "thinking")
                                    if next_remaining[next_end + len("</thinking>") :]:
                                        yield (
                                            next_remaining[next_end + len("</thinking>") :],
                                            None,
                                        )
                                else:
                                    if next_remaining:
                                        yield (next_remaining, "thinking")
                                        in_thinking = True
                            else:
                                yield (after_end, None)
                    else:
                        # 只有开始标签，立即流式输出剩余内容
                        if remaining:
                            yield (remaining, "thinking")
                else:
                    # 检测部分 <thinking> 标签（可能跨 chunk）
                    if (
                        combined.endswith("<")
                        or combined.endswith("<t")
                        or (combined.endswith("<th") and "<thinking>" not in combined)
                    ):
                        # 可能是 <thinking> 标签的开始，保存待下次处理
                        pending_buffer = combined
                    elif combined.startswith("<") and not combined.startswith("<thinking>"):
                        # 其他标签开头，暂存
                        pending_buffer = combined
                    else:
                        # 正常内容，流式输出
                        yield (combined, None)
            else:
                # 在思考模式中，检测 </thinking> 标签
                thinking_end = combined.find("</thinking>")
                if thinking_end != -1:
                    # 找到结束标签，输出之前的思考内容
                    before_end = combined[:thinking_end]
                    if before_end:
                        yield (before_end, "thinking")
                    in_thinking = False
                    # 结束标签后的内容
                    after_end = combined[thinking_end + len("</thinking>") :]
                    if after_end:
                        # 递归检查是否还有嵌套标签
                        next_thinking = after_end.find("<thinking>")
                        if next_thinking != -1:
                            if next_thinking > 0:
                                yield (after_end[:next_thinking], None)
                            next_remaining = after_end[next_thinking + len("<thinking>") :]
                            next_end = next_remaining.find("</thinking>")
                            if next_end != -1:
                                if next_remaining[:next_end]:
                                    yield (next_remaining[:next_end], "thinking")
                                if next_remaining[next_end + len("</thinking>") :]:
                                    yield (
                                        next_remaining[next_end + len("</thinking>") :],
                                        None,
                                    )
                            else:
                                if next_remaining:
                                    yield (next_remaining, "thinking")
                                    in_thinking = True
                        else:
                            yield (after_end, None)
                else:
                    # 仍在思考模式中，立即流式输出思考内容
                    if combined:
                        yield (combined, "thinking")

        # 处理剩余内容
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
            Optional[Any],
        ],
        None,
    ]:
        """
        执行完整的 Multi-Agent 分析流程，流式输出进度

        流程：
        1. FundamentalAgent + TechnicalAgent 并行分析（各自负责获取数据）
        2. 等待两个 Agent 都完成
        3. CoordinatorAgent 综合分析（返回流式生成器）

        Yields:
            (event_type, state, stream_gen, message, data) 元组
            - event_type: 事件类型（如 "fundamental_analyzer:running"）
            - state: 当前分析状态
            - stream_gen: 综合分析的流式生成器（仅在 coordinator 时有值）
            - message: 进度消息文案
            - data: 可选的附加数据（如因子列表）
        """
        # 初始化状态
        state = AnalysisState(symbol=symbol.upper())

        # 步骤 1: 并行执行基本面和技术面分析（各自负责获取数据）
        progress_queue: asyncio.Queue = asyncio.Queue()

        async def wrapped_fundamental():
            """透传 fundamental agent 的状态回调"""
            await self.fundamental_agent.analyze(
                state,
                progress_callback=lambda step, status, message, data: progress_queue.put(
                    (step, status, message, data)
                ),
            )

        async def wrapped_technical():
            """透传 technical agent 的状态回调"""
            await self.technical_agent.analyze(
                state,
                progress_callback=lambda step, status, message, data: progress_queue.put(
                    (step, status, message, data)
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
                step, status, message, data = event
                # 透传子 Agent 的状态（第5个元素是 data）
                yield (f"{step}:{status}", state, None, message, data)
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

        # 步骤 2: 返回综合分析的流式生成器
        yield (
            "coordinator:running",
            state,
            self.coordinator.synthesize_stream(state),
            "正在生成综合报告...",
            None,
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
        async for (
            _event_type,
            event_state,
            event_stream_gen,
            _event_message,
            _event_data,
        ) in self.analyze_stream(symbol):
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
