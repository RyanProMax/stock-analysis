"""
DataAgent - 数据获取 Agent

负责获取股票数据，不使用 LLM，直接调用 stock_service
"""

from typing import Optional, List, Any, Callable
from ..base import BaseAgent, AnalysisState
from ...service.stock_service import stock_service


def convert_factors_to_dict(factors: Any) -> List[dict]:
    """将因子对象转换为字典，符合前端 FactorDetail 接口"""
    result = []
    for factor in factors or []:
        if hasattr(factor, "name"):
            result.append(
                {
                    "name": getattr(factor, "name", ""),
                    "key": getattr(factor, "key", ""),
                    "status": getattr(factor, "status", ""),
                    "bullish_signals": list(getattr(factor, "bullish_signals", [])),
                    "bearish_signals": list(getattr(factor, "bearish_signals", [])),
                }
            )
    return result


class DataAgent(BaseAgent):
    """
    数据获取 Agent

    职责：
    - 获取股票价格数据
    - 获取股票基本信息（名称、行业等）
    - 准备后续分析所需的数据
    """

    def __init__(self):
        super().__init__(llm_manager=None)
        self.set_name("DataAgent")

    async def analyze(
        self, state: AnalysisState, progress_callback: Optional[Callable] = None
    ) -> AnalysisState:
        """
        获取股票数据

        Args:
            state: 包含 symbol 的分析状态
            progress_callback: 进度回调函数

        Returns:
            更新了数据的分析状态
        """
        self._start_timing()

        if progress_callback:
            await progress_callback(f"正在获取 {state.symbol} 数据...")

        try:
            # 调用现有的 stock_service 获取完整分析报告
            report = stock_service.analyze_symbol(state.symbol)

            if not report:
                state.set_error(self.get_name(), f"无法获取 {state.symbol} 的数据")
                return state

            # 更新状态
            state.stock_name = report.stock_name or ""
            state.industry = report.industry or ""
            state.price = report.price or 0.0
            state.stock_data = report

            # 保存因子数据（供后续 Agent 使用）
            state.fundamental_factors = convert_factors_to_dict(report.fundamental_factors)
            state.technical_factors = convert_factors_to_dict(report.technical_factors)

        except Exception as e:
            state.set_error(self.get_name(), f"数据获取失败: {str(e)}")

        execution_time = self._end_timing()
        state.set_execution_time(self.get_name(), execution_time)

        return state

    async def fetch_data(self, symbol: str, refresh: bool = False) -> Optional[AnalysisState]:
        """
        便捷方法：直接获取数据并返回新状态

        Args:
            symbol: 股票代码
            refresh: 是否强制刷新缓存

        Returns:
            包含数据的 AnalysisState，或 None（失败时）
        """
        state = AnalysisState(symbol=symbol.upper())
        await self.analyze(state)
        return state if not state.has_error(self.get_name()) else None
