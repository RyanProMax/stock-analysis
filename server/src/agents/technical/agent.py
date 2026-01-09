"""
TechnicalAgent - 技术面分析 Agent

负责技术面分析，使用专门的 LLM prompt 生成独立分析结论
"""

from typing import Optional, Callable, List
from openai.types.chat import ChatCompletionMessageParam

from ..base import BaseAgent, AnalysisState
from .prompts import (
    TECHNICAL_SYSTEM_MESSAGE,
    build_technical_prompt,
)


class TechnicalAgent(BaseAgent):
    """
    技术面分析 Agent

    职责：
    - 分析技术面因子数据
    - 使用专门的 LLM prompt 生成技术面分析结论
    - 提供独立的投资建议（仅基于技术面）
    """

    def __init__(self, llm_manager):
        super().__init__(llm_manager=llm_manager)
        self.set_name("TechnicalAgent")

    async def analyze(
        self, state: AnalysisState, progress_callback: Optional[Callable] = None
    ) -> AnalysisState:
        """
        执行技术面分析

        Args:
            state: 包含技术面数据的分析状态
            progress_callback: 进度回调函数

        Returns:
            更新了技术面分析结论的状态
        """
        self._start_timing()

        if progress_callback:
            await progress_callback("正在分析技术面...")

        # 检查是否有数据
        if not state.technical_factors:
            state.set_error(self.get_name(), "缺少技术面因子数据")
            return state

        try:
            # 构建分析 prompt
            user_prompt = build_technical_prompt(
                symbol=state.symbol,
                stock_name=state.stock_name,
                technical_factors=state.technical_factors,
            )

            # 调用 LLM 生成分析
            messages: List[ChatCompletionMessageParam] = [
                {"role": "system", "content": TECHNICAL_SYSTEM_MESSAGE},
                {"role": "user", "content": user_prompt},
            ]

            analysis = await self._call_llm(messages, temperature=1.0)
            state.technical_analysis = analysis

        except Exception as e:
            state.set_error(self.get_name(), f"技术面分析失败: {str(e)}")

        execution_time = self._end_timing()
        state.set_execution_time(self.get_name(), execution_time)

        return state
