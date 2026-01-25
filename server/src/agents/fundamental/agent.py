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
            assert self.llm is not None  # Type narrowing

            full_response = ""
            thinking_response = ""

            # LLM 返回 (content, reasoning) 元组
            # DeepSeek: reasoning 包含推理过程
            # 其他模型: reasoning 为空
            async for content, reasoning in self.llm.chat_completion_stream(
                messages=messages,
                temperature=1.0,
            ):
                if reasoning:
                    thinking_response += reasoning
                    yield (reasoning, "thinking")
                if content:
                    full_response += content
                    yield (content, None)

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
