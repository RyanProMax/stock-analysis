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
            progress_callback: 进度回调函数 callback(step, status, message, data)

        Returns:
            更新了技术面分析结论的状态
        """
        self._start_timing()

        # 数据获取阶段
        if progress_callback:
            await progress_callback(
                "technical_analyzer", "fetching", f"正在获取 {state.symbol} 技术面数据...", None
            )

        if state.technical_factors is None:
            state.set_error(self.get_name(), "技术面数据不可用")
            if progress_callback:
                await progress_callback("technical_analyzer", "error", "技术面数据不可用", None)
            return state

        if progress_callback:
            await progress_callback("technical_analyzer", "data_ready", "技术面数据获取完成", None)
            await progress_callback("technical_analyzer", "running", "正在分析技术面...", None)

        try:
            # 构建分析 prompt
            user_prompt = build_technical_prompt(
                symbol=state.symbol,
                stock_name=state.stock_name,
                technical_factors=state.technical_factors,
            )

            messages: List[ChatCompletionMessageParam] = [
                {"role": "system", "content": TECHNICAL_SYSTEM_MESSAGE},
                {"role": "user", "content": user_prompt},
            ]

            if progress_callback:
                await progress_callback("technical_analyzer", "analyzing", "LLM 正在推理...", None)

            analysis = await self._call_llm(messages, temperature=1.0)
            state.technical_analysis = analysis

        except Exception as e:
            state.set_error(self.get_name(), f"技术面分析失败: {str(e)}")
            if progress_callback:
                await progress_callback(
                    "technical_analyzer", "error", state.errors[self.get_name()], None
                )

        execution_time = self._end_timing()
        state.set_execution_time(self.get_name(), execution_time)

        if progress_callback and not state.has_error(self.get_name()):
            await progress_callback("technical_analyzer", "success", "技术面分析完成", None)

        return state
