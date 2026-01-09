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
            progress_callback: 进度回调函数

        Returns:
            更新了基本面分析结论的状态
        """
        self._start_timing()

        if progress_callback:
            await progress_callback("正在分析基本面...")

        # 检查是否有数据
        if not state.fundamental_factors:
            state.set_error(self.get_name(), "缺少基本面因子数据")
            return state

        try:
            # 构建分析 prompt
            user_prompt = build_fundamental_prompt(
                symbol=state.symbol,
                stock_name=state.stock_name,
                industry=state.industry,
                fundamental_factors=state.fundamental_factors,
            )

            # 调用 LLM 生成分析
            messages: List[ChatCompletionMessageParam] = [
                {"role": "system", "content": FUNDAMENTAL_SYSTEM_MESSAGE},
                {"role": "user", "content": user_prompt},
            ]

            analysis = await self._call_llm(messages, temperature=1.0)
            state.fundamental_analysis = analysis

        except Exception as e:
            state.set_error(self.get_name(), f"基本面分析失败: {str(e)}")

        execution_time = self._end_timing()
        state.set_execution_time(self.get_name(), execution_time)

        return state
