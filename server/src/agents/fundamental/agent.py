"""
FundamentalAgent - 基本面分析 Agent

负责基本面分析，使用专门的 LLM prompt 生成独立分析结论
"""

from typing import Optional, Callable, List
from openai.types.chat import ChatCompletionMessageParam

from ..base import BaseAgent, AnalysisState
from .prompts import (
    FUNDAMENTAL_SYSTEM_MESSAGE,
    build_fundamental_prompt,
)


class FundamentalAgent(BaseAgent):
    """
    基本面分析 Agent

    职责：
    - 分析基本面因子数据
    - 使用专门的 LLM prompt 生成基本面分析结论
    - 提供独立的投资建议（仅基于基本面）
    """

    def __init__(self, llm_manager):
        super().__init__(llm_manager=llm_manager)
        self.set_name("FundamentalAgent")

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

        # 数据获取阶段
        if progress_callback:
            await progress_callback(
                "fundamental_analyzer", "fetching", f"正在获取 {state.symbol} 基本面数据...", None
            )

        if state.fundamental_factors is None:
            state.set_error(self.get_name(), "基本面数据不可用")
            if progress_callback:
                await progress_callback("fundamental_analyzer", "error", "基本面数据不可用", None)
            return state

        if progress_callback:
            await progress_callback(
                "fundamental_analyzer", "data_ready", "基本面数据获取完成", None
            )
            await progress_callback("fundamental_analyzer", "running", "正在分析基本面...", None)

        try:
            # 构建分析 prompt
            user_prompt = build_fundamental_prompt(
                symbol=state.symbol,
                stock_name=state.stock_name,
                industry=state.industry,
                fundamental_factors=state.fundamental_factors,
            )

            messages: List[ChatCompletionMessageParam] = [
                {"role": "system", "content": FUNDAMENTAL_SYSTEM_MESSAGE},
                {"role": "user", "content": user_prompt},
            ]

            if progress_callback:
                await progress_callback(
                    "fundamental_analyzer", "analyzing", "LLM 正在推理...", None
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
            await progress_callback("fundamental_analyzer", "success", "基本面分析完成", None)

        return state
