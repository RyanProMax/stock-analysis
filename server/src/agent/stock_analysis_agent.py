"""
LangGraph 股票分析 Agent
"""

from typing import Dict, Any, List, Optional, TypedDict, Annotated, Sequence
from datetime import datetime
import json
import asyncio
import operator

from langgraph.graph import StateGraph, END
from openai.types.chat import ChatCompletionMessageParam

from ..service.stock_service import stock_service
from . import prompts
from .llm import LLMManager


class AgentState(TypedDict):
    """Agent状态定义"""

    symbol: str
    messages: Annotated[Sequence[dict], "消息历史"]
    current_step: str
    error: Optional[str]

    # 存储各类分析结果
    fundamental_data: Optional[Any]
    technical_data: Optional[Any]
    qlib_data: Optional[Any]
    fear_greed: Optional[Any]

    # 最终结果
    analysis_result: Optional[Dict[str, Any]]

    # 进度追踪
    progress: Annotated[List[Dict[str, Any]], operator.add]


class StockAnalysisAgent:
    """股票分析Agent"""

    def __init__(self):
        """初始化Agent"""
        self.graph = self._build_graph()
        self.llm_manager = LLMManager()
        self.use_llm = self.llm_manager.is_available

    def _build_graph(self) -> Any:
        """构建LangGraph工作流"""
        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node("data_fetcher", self._data_fetcher_node)
        workflow.add_node("fundamental_analyzer", self._fundamental_analysis_node)
        workflow.add_node("technical_analyzer", self._technical_analysis_node)
        workflow.add_node("qlib_analyzer", self._qlib_analysis_node)
        workflow.add_node("decision_maker", self._decision_maker_node)

        # 设置流程
        workflow.set_entry_point("data_fetcher")
        workflow.add_edge("data_fetcher", "fundamental_analyzer")
        workflow.add_edge("data_fetcher", "technical_analyzer")
        workflow.add_edge("data_fetcher", "qlib_analyzer")
        workflow.add_edge("fundamental_analyzer", "decision_maker")
        workflow.add_edge("technical_analyzer", "decision_maker")
        workflow.add_edge("qlib_analyzer", "decision_maker")
        workflow.add_edge("decision_maker", END)

        return workflow.compile()

    def _add_progress(self, state: AgentState, step: str, status: str, message: str):
        """添加进度记录"""
        state["progress"].append(
            {
                "step": step,
                "status": status,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def _data_fetcher_node(self, state: AgentState) -> AgentState:
        """数据获取节点"""
        try:
            symbol = state["symbol"]
            self._add_progress(state, "data_fetcher", "running", f"正在获取 {symbol} 数据...")

            # 获取完整分析报告
            report = stock_service.analyze_symbol(symbol)
            if not report:
                state["error"] = "无法获取数据"
                self._add_progress(state, "data_fetcher", "error", f"数据获取失败")
                return state

            # 直接存储原始数据
            state["fundamental_data"] = report.fundamental_factors
            state["technical_data"] = report.technical_factors
            state["qlib_data"] = report.qlib_factors
            state["fear_greed"] = report.fear_greed

            self._add_progress(state, "data_fetcher", "success", f"成功获取 {symbol} 数据")
            return state

        except Exception as e:
            state["error"] = str(e)
            self._add_progress(state, "data_fetcher", "error", f"数据获取异常: {str(e)}")
            return state

    def _fundamental_analysis_node(self, state: AgentState) -> AgentState:
        """基本面分析节点"""
        try:
            self._add_progress(state, "fundamental_analyzer", "running", "基本面分析中...")
            # 数据已在 data_fetcher 获取，直接使用
            self._add_progress(state, "fundamental_analyzer", "success", "基本面分析完成")
            return state
        except Exception as e:
            state["error"] = str(e)
            self._add_progress(state, "fundamental_analyzer", "error", f"基本面分析异常: {str(e)}")
            return state

    def _technical_analysis_node(self, state: AgentState) -> AgentState:
        """技术面分析节点"""
        try:
            self._add_progress(state, "technical_analyzer", "running", "技术面分析中...")
            # 数据已在 data_fetcher 获取，直接使用
            self._add_progress(state, "technical_analyzer", "success", "技术面分析完成")
            return state
        except Exception as e:
            state["error"] = str(e)
            self._add_progress(state, "technical_analyzer", "error", f"技术面分析异常: {str(e)}")
            return state

    def _qlib_analysis_node(self, state: AgentState) -> AgentState:
        """Qlib分析节点"""
        try:
            self._add_progress(state, "qlib_analyzer", "running", "Qlib因子分析中...")
            # 数据已在 data_fetcher 获取，直接使用
            self._add_progress(state, "qlib_analyzer", "success", "Qlib因子分析完成")
            return state
        except Exception as e:
            state["error"] = str(e)
            self._add_progress(state, "qlib_analyzer", "error", f"Qlib分析异常: {str(e)}")
            return state

    def _decision_maker_node(self, state: AgentState) -> AgentState:
        """决策节点"""
        try:
            self._add_progress(state, "decision_maker", "running", "生成投资建议...")

            # 准备给LLM的数据
            fundamental_data = state.get("fundamental_data") or []
            technical_data = state.get("technical_data") or []
            qlib_data = state.get("qlib_data") or []
            fear_greed = state.get("fear_greed")

            llm_data = {
                "symbol": state["symbol"],
                "fundamental_factors": self._convert_factors_to_dict(fundamental_data),
                "technical_factors": self._convert_factors_to_dict(technical_data),
                "qlib_factors": self._convert_qlib_factors_to_dict(qlib_data),
                "fear_greed": {
                    "index": fear_greed.index if fear_greed else 50,
                    "label": fear_greed.label if fear_greed else "中性",
                },
            }

            # 构建prompt
            prompt = json.dumps(llm_data, indent=2, ensure_ascii=False)

            # 调用LLM
            if self.use_llm:
                messages: List[ChatCompletionMessageParam] = [
                    {"role": "system", "content": prompts.DECISION_SYSTEM_MESSAGE},
                    {
                        "role": "user",
                        "content": f"请分析股票数据并给出建议：\n\n{prompt}",
                    },
                ]

                llm_output = asyncio.run(
                    self.llm_manager.chat_completion(
                        messages=messages, temperature=0.3, max_tokens=1000
                    )
                )

                # 简单解析LLM输出
                decision = {"action": "分析完成", "analysis": llm_output}
            else:
                decision = {"action": "无LLM", "analysis": "LLM未配置"}

            state["analysis_result"] = {
                "symbol": state["symbol"],
                "timestamp": datetime.now().isoformat(),
                "decision": decision,
            }

            self._add_progress(state, "decision_maker", "success", "投资建议生成完成")
            return state

        except Exception as e:
            state["error"] = str(e)
            self._add_progress(state, "decision_maker", "error", f"决策分析异常: {str(e)}")
            return state

    def _convert_factors_to_dict(self, factors: Any) -> List[Dict]:
        """将因子对象转换为字典"""
        result = []
        if not factors:
            return result

        for factor in factors:
            if hasattr(factor, "name"):
                result.append(
                    {
                        "name": getattr(factor, "name", ""),
                        "key": getattr(factor, "key", ""),
                        "status": getattr(factor, "status", ""),
                        "bullish": list(getattr(factor, "bullish_signals", [])),
                        "bearish": list(getattr(factor, "bearish_signals", [])),
                    }
                )
        return result

    def _convert_qlib_factors_to_dict(self, factors: Any) -> List[Dict]:
        """将Qlib因子转换为字典"""
        result = []
        if not factors:
            return result

        for factor in factors:
            if hasattr(factor, "name"):
                result.append(
                    {
                        "name": getattr(factor, "name", ""),
                        "key": getattr(factor, "key", ""),
                        "value": getattr(factor, "status", ""),
                    }
                )
        return result

    def run_analysis(self, symbol: str):
        """运行分析"""
        initial_state = AgentState(
            symbol=symbol,
            messages=[],
            current_step="",
            error=None,
            fundamental_data=None,
            technical_data=None,
            qlib_data=None,
            fear_greed=None,
            analysis_result=None,
            progress=[],
        )

        for output in self.graph.stream(initial_state):
            yield output
