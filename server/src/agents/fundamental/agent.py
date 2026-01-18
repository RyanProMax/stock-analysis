"""
FundamentalAgent - 基本面分析 Agent

负责基本面分析，使用专门的 LLM prompt 生成独立分析结论
"""

from typing import Optional, Callable, List, AsyncGenerator, Tuple
from openai.types.chat import ChatCompletionMessageParam

from ..base import BaseAgent, AnalysisState
from ...services.stock_service import stock_service
from .prompts import (
    FUNDAMENTAL_SYSTEM_MESSAGE,
    build_fundamental_prompt,
)


class FundamentalAgent(BaseAgent):
    """
    基本面分析 Agent

    职责：
    - 获取股票数据（如果尚未获取）
    - 分析基本面因子数据
    - 使用专门的 LLM prompt 生成基本面分析结论
    - 提供独立的投资建议（仅基于基本面）
    """

    def __init__(self, llm_manager):
        super().__init__(llm_manager=llm_manager)
        self.set_name("FundamentalAgent")

    async def _fetch_stock_data(self, state: AnalysisState) -> bool:
        """
        获取股票数据

        Args:
            state: 分析状态

        Returns:
            是否获取成功
        """
        try:
            report = stock_service.analyze_symbol(state.symbol)
            if not report:
                return False

            # 更新状态
            state.stock_name = report.stock_name or ""
            state.industry = report.industry or ""
            state.price = report.price or 0.0
            state.stock_data = report

            # 保存因子数据（直接使用 FactorAnalysis）
            state.fundamental = report.fundamental
            state.technical = report.technical

            # 标记数据已获取
            state._data_fetched = True
            return True
        except Exception:
            return False

    async def analyze_stream(
        self, state: AnalysisState, progress_callback: Optional[Callable] = None
    ) -> AsyncGenerator[Tuple[str, Optional[str]], None]:
        """
        执行基本面分析并流式输出结果

        Args:
            state: 包含基本面数据的分析状态
            progress_callback: 进度回调函数 callback(step, status, message, data)

        Yields:
            (content, thinking_type) 元组
            - content: LLM 生成的文本片段
            - thinking_type: None 表示正常内容, "thinking" 表示思考过程
        """
        self._start_timing()

        # 数据获取阶段（如果尚未获取）
        if not state._data_fetched:
            if progress_callback:
                await progress_callback(
                    "fundamental_analyzer",
                    "fetching",
                    f"正在获取 {state.symbol} 数据...",
                    None,
                )

            if not await self._fetch_stock_data(state):
                state.set_error(self.get_name(), f"无法获取 {state.symbol} 的数据")
                if progress_callback:
                    await progress_callback("fundamental_analyzer", "error", "数据获取失败", None)
                yield ("数据获取失败", None)
                return

        if state.fundamental is None:
            state.set_error(self.get_name(), "基本面数据不可用")
            if progress_callback:
                await progress_callback("fundamental_analyzer", "error", "基本面数据不可用", None)
            yield ("基本面数据不可用", None)
            return

        if progress_callback:
            await progress_callback(
                "fundamental_analyzer",
                "running",
                "正在分析基本面...",
                state.fundamental,
            )

        try:
            # 构建分析 prompt
            user_prompt = build_fundamental_prompt(
                symbol=state.symbol,
                stock_name=state.stock_name,
                industry=state.industry,
                fundamental=state.fundamental,
            )

            messages: List[ChatCompletionMessageParam] = [
                {"role": "system", "content": FUNDAMENTAL_SYSTEM_MESSAGE},
                {"role": "user", "content": user_prompt},
            ]

            if progress_callback:
                await progress_callback(
                    "fundamental_analyzer", "analyzing", "LLM 正在推理基本面...", None
                )

            # 流式输出 LLM 响应
            if not self.llm or not self.llm.is_available:
                yield ("LLM 未配置", None)
                return

            assert self.llm is not None  # Type narrowing

            # 标签常量
            THINKING_START = "<thinking>"
            THINKING_END = "</thinking>"
            THINKING_START_LEN = len(THINKING_START)
            THINKING_END_LEN = len(THINKING_END)

            in_thinking = False
            pending_buffer = ""
            full_response = ""
            thinking_response = ""

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

            def process_after_end(content: str) -> List[Tuple[str, Optional[str]]]:
                """处理结束标签后的内容，检查嵌套的 thinking 标签"""
                nonlocal in_thinking
                results = []
                if not content:
                    return results

                next_thinking = content.find(THINKING_START)
                if next_thinking != -1:
                    if next_thinking > 0:
                        results.append((content[:next_thinking], None))
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

            async for chunk in self.llm.chat_completion_stream(
                messages=messages,
                temperature=1.0,
            ):
                combined = pending_buffer + chunk
                pending_buffer = ""

                if not in_thinking:
                    # 检测 <thinking> 标签开始
                    thinking_start = combined.find(THINKING_START)
                    if thinking_start != -1:
                        # 输出标签之前的内容
                        if thinking_start > 0:
                            content = combined[:thinking_start]
                            full_response += content
                            yield (content, None)
                        in_thinking = True
                        # 标签之后的内容
                        remaining = combined[thinking_start + THINKING_START_LEN :]
                        # 检查是否在同一 chunk 中有结束标签
                        thinking_end = remaining.find(THINKING_END)
                        if thinking_end != -1:
                            thinking_content = remaining[:thinking_end]
                            if thinking_content:
                                thinking_response += thinking_content
                                yield (thinking_content, "thinking")
                            in_thinking = False
                            # 处理结束标签后的内容
                            after_end = remaining[thinking_end + THINKING_END_LEN :]
                            for result in process_after_end(after_end):
                                if result[1] == "thinking":
                                    thinking_response += result[0]
                                else:
                                    full_response += result[0]
                                yield result
                        else:
                            # 只有开始标签，输出剩余内容
                            if remaining:
                                thinking_response += remaining
                                yield (remaining, "thinking")
                    elif is_partial_start_tag(combined) or (
                        combined.startswith("<") and not combined.startswith(THINKING_START)
                    ):
                        # 部分标签或其他标签开头，保存待下次处理
                        pending_buffer = combined
                    else:
                        # 正常内容，流式输出
                        full_response += combined
                        yield (combined, None)
                else:
                    # 在思考模式中，检测 </thinking> 标签
                    thinking_end = combined.find(THINKING_END)
                    if thinking_end != -1:
                        # 找到结束标签，输出之前的思考内容
                        before_end = combined[:thinking_end]
                        if before_end:
                            thinking_response += before_end
                            yield (before_end, "thinking")
                        in_thinking = False
                        # 处理结束标签后的内容
                        after_end = combined[thinking_end + THINKING_END_LEN :]
                        for result in process_after_end(after_end):
                            if result[1] == "thinking":
                                thinking_response += result[0]
                            else:
                                full_response += result[0]
                            yield result
                    elif is_partial_end_tag(combined):
                        # 部分结束标签，保存待下次处理
                        pending_buffer = combined
                    else:
                        # 仍在思考模式中，输出思考内容
                        if combined:
                            thinking_response += combined
                            yield (combined, "thinking")

            # 处理剩余内容
            if pending_buffer:
                if in_thinking:
                    thinking_response += pending_buffer
                else:
                    full_response += pending_buffer
                yield (pending_buffer, "thinking" if in_thinking else None)

            # 保存完整结果到状态
            state.fundamental_analysis = full_response
            state.thinking_process = thinking_response

        except Exception as e:
            error_msg = f"基本面分析失败: {str(e)}"
            state.set_error(self.get_name(), error_msg)
            if progress_callback:
                await progress_callback("fundamental_analyzer", "error", error_msg, None)
            yield (error_msg, None)

        execution_time = self._end_timing()
        state.set_execution_time(self.get_name(), execution_time)

        if progress_callback and not state.has_error(self.get_name()):
            await progress_callback(
                "fundamental_analyzer",
                "completed",
                "基本面分析完成",
                {"execution_time": execution_time},
            )

    async def analyze(
        self, state: AnalysisState, progress_callback: Optional[Callable] = None
    ) -> AnalysisState:
        """
        执行基本面分析

        Args:
            state: 包含基本面数据的分析状态
            progress_callback: 进度回调函数 callback(step, status, message, data)

        Returns:
            更新了基本面分析结论的状态
        """
        self._start_timing()

        # 数据获取阶段（如果尚未获取）
        if not state._data_fetched:
            if progress_callback:
                await progress_callback(
                    "fundamental_analyzer",
                    "fetching",
                    f"正在获取 {state.symbol} 数据...",
                    None,
                )

            if not await self._fetch_stock_data(state):
                state.set_error(self.get_name(), f"无法获取 {state.symbol} 的数据")
                if progress_callback:
                    await progress_callback("fundamental_analyzer", "error", "数据获取失败", None)
                return state

        if state.fundamental is None:
            state.set_error(self.get_name(), "基本面数据不可用")
            if progress_callback:
                await progress_callback("fundamental_analyzer", "error", "基本面数据不可用", None)
            return state

        if progress_callback:
            await progress_callback(
                "fundamental_analyzer",
                "running",
                "正在分析基本面...",
                state.fundamental,
            )

        try:
            # 构建分析 prompt
            user_prompt = build_fundamental_prompt(
                symbol=state.symbol,
                stock_name=state.stock_name,
                industry=state.industry,
                fundamental=state.fundamental,
            )

            messages: List[ChatCompletionMessageParam] = [
                {"role": "system", "content": FUNDAMENTAL_SYSTEM_MESSAGE},
                {"role": "user", "content": user_prompt},
            ]

            if progress_callback:
                await progress_callback(
                    "fundamental_analyzer", "analyzing", "LLM 正在推理基本面...", None
                )

            analysis = await self._call_llm(messages, temperature=1.0)
            state.fundamental_analysis = analysis

        except Exception as e:
            state.set_error(self.get_name(), f"基本面分析失败: {str(e)}")
            if progress_callback:
                await progress_callback(
                    "fundamental_analyzer", "error", state.errors[self.get_name()], None
                )

        execution_time = self._end_timing()
        state.set_execution_time(self.get_name(), execution_time)

        if progress_callback and not state.has_error(self.get_name()):
            await progress_callback(
                "fundamental_analyzer",
                "completed",
                "基本面分析完成",
                {"execution_time": execution_time},
            )

        return state
