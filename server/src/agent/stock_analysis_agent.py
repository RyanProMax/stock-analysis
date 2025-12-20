"""
LangGraph 股票分析 Agent

将基础面、技术面、Qlib因子分析抽离成不同的Node，通过LangGraph构建可扩展的工作流。
"""

from typing import Dict, Any, List, Optional, TypedDict, Annotated, Sequence, Union
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_core.pydantic_v1 import BaseModel, Field

from ..service.stock_service import stock_service


class AgentState(TypedDict):
    """Agent状态定义"""

    symbol: str
    messages: Annotated[Sequence[dict], "消息历史"]
    current_step: str
    error: Optional[str]

    # 各节点分析结果
    fundamental_data: Optional[Dict[str, Any]]
    technical_data: Optional[Dict[str, Any]]
    qlib_data: Optional[Dict[str, Any]]

    # 最终分析结果
    analysis_result: Optional[Dict[str, Any]]

    # 流式输出状态
    progress: Annotated[List[Dict[str, Any]], "进度信息"]


class NodeOutput(BaseModel):
    """节点输出格式"""

    status: str = Field(description="节点执行状态: success/error")
    data: Optional[Dict[str, Any]] = Field(description="节点分析结果")
    error: Optional[str] = Field(description="错误信息")
    progress: Dict[str, Any] = Field(description="进度信息")


class StockAnalysisAgent:
    """股票分析Agent"""

    def __init__(self):
        """初始化Agent"""
        self.graph = self._build_graph()

    def _build_graph(self) -> Any:
        """构建LangGraph工作流"""

        # 创建状态图
        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node("data_fetcher", self._data_fetcher_node)
        workflow.add_node("fundamental_analyzer", self._fundamental_analysis_node)
        workflow.add_node("technical_analyzer", self._technical_analysis_node)
        workflow.add_node("qlib_analyzer", self._qlib_analysis_node)
        workflow.add_node("decision_maker", self._decision_maker_node)

        # 设置入口
        workflow.set_entry_point("data_fetcher")

        # 定义执行流程
        workflow.add_edge("data_fetcher", "fundamental_analyzer")
        workflow.add_edge("fundamental_analyzer", "technical_analyzer")
        workflow.add_edge("technical_analyzer", "qlib_analyzer")
        workflow.add_edge("qlib_analyzer", "decision_maker")
        workflow.add_edge("decision_maker", END)

        return workflow.compile()

    def _data_fetcher_node(self, state: AgentState) -> AgentState:
        """数据获取节点 - 准备所有必要的数据"""
        try:
            symbol = state["symbol"]

            # 更新进度
            progress_entry = {
                "step": "data_fetcher",
                "status": "running",
                "message": f"正在获取股票 {symbol} 的基础数据...",
                "timestamp": datetime.now().isoformat(),
            }
            state["progress"].append(progress_entry)
            state["current_step"] = "data_fetcher"

            # 获取股票数据
            result = stock_service.get_analysis_data_for_agent(symbol)

            if not result["success"]:
                state["error"] = result.get("error", "数据获取失败")
                progress_entry["status"] = "error"
                progress_entry["message"] = f"数据获取失败: {state['error']}"
                return state

            # 存储数据供后续节点使用
            data = result["data"]
            state["fundamental_data"] = {
                "financial_data": data.get("financial_data") or {},
                "basic_info": data.get("basic_info") or {},
            }
            state["technical_data"] = {
                "stock_data": data.get("stock_data") or {},
                "market_data": data.get("market_data") or {},
            }

            # 更新进度
            progress_entry["status"] = "success"
            progress_entry["message"] = f"成功获取股票 {symbol} 的基础数据"
            state["progress"].append(progress_entry)

            return state

        except Exception as e:
            state["error"] = str(e)
            state["progress"].append(
                {
                    "step": "data_fetcher",
                    "status": "error",
                    "message": f"数据获取异常: {str(e)}",
                    "timestamp": datetime.now().isoformat(),
                }
            )
            return state

    def _fundamental_analysis_node(self, state: AgentState) -> AgentState:
        """基本面分析节点"""
        try:
            symbol = state["symbol"]

            # 更新进度
            state["progress"].append(
                {
                    "step": "fundamental_analyzer",
                    "status": "running",
                    "message": "正在进行基本面分析...",
                    "timestamp": datetime.now().isoformat(),
                }
            )
            state["current_step"] = "fundamental_analyzer"

            # 获取基本面因子
            result = stock_service.get_fundamental_factors_for_agent(symbol)

            if result["success"]:
                factors = result["data"]

                # 转换为结构化数据
                fundamental_analysis = {
                    "factors": [],
                    "summary": {
                        "total_factors": len(factors),
                        "bullish_count": 0,
                        "bearish_count": 0,
                    },
                }

                for factor in factors:
                    factor_dict = {
                        "name": factor.name,
                        "key": factor.key,
                        "status": factor.status,
                        "bullish_signals": [s.model_dump() for s in factor.bullish_signals],
                        "bearish_signals": [s.model_dump() for s in factor.bearish_signals],
                    }
                    fundamental_analysis["factors"].append(factor_dict)

                    if factor.bullish_signals:
                        fundamental_analysis["summary"]["bullish_count"] += 1
                    if factor.bearish_signals:
                        fundamental_analysis["summary"]["bearish_count"] += 1

                if state["fundamental_data"] is not None:
                    state["fundamental_data"]["analysis"] = fundamental_analysis

                # 更新进度
                state["progress"].append(
                    {
                        "step": "fundamental_analyzer",
                        "status": "success",
                        "message": f"基本面分析完成，共分析 {len(factors)} 个因子",
                        "data": fundamental_analysis["summary"],
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            else:
                state["error"] = result.get("error", "基本面分析失败")
                state["progress"].append(
                    {
                        "step": "fundamental_analyzer",
                        "status": "error",
                        "message": f"基本面分析失败: {state['error']}",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            return state

        except Exception as e:
            state["error"] = str(e)
            state["progress"].append(
                {
                    "step": "fundamental_analyzer",
                    "status": "error",
                    "message": f"基本面分析异常: {str(e)}",
                    "timestamp": datetime.now().isoformat(),
                }
            )
            return state

    def _technical_analysis_node(self, state: AgentState) -> AgentState:
        """技术面分析节点"""
        try:
            symbol = state["symbol"]

            # 更新进度
            state["progress"].append(
                {
                    "step": "technical_analyzer",
                    "status": "running",
                    "message": "正在进行技术面分析...",
                    "timestamp": datetime.now().isoformat(),
                }
            )
            state["current_step"] = "technical_analyzer"

            # 获取技术面因子
            result = stock_service.get_technical_factors_for_agent(symbol)

            if result["success"]:
                factors = result["data"]

                # 转换为结构化数据
                technical_analysis = {
                    "factors": [],
                    "summary": {
                        "total_factors": len(factors),
                        "bullish_count": 0,
                        "bearish_count": 0,
                    },
                }

                for factor in factors:
                    factor_dict = {
                        "name": factor.name,
                        "key": factor.key,
                        "status": factor.status,
                        "bullish_signals": [s.model_dump() for s in factor.bullish_signals],
                        "bearish_signals": [s.model_dump() for s in factor.bearish_signals],
                    }
                    technical_analysis["factors"].append(factor_dict)

                    if factor.bullish_signals:
                        technical_analysis["summary"]["bullish_count"] += 1
                    if factor.bearish_signals:
                        technical_analysis["summary"]["bearish_count"] += 1

                if state["technical_data"] is not None:
                    state["technical_data"]["analysis"] = technical_analysis

                # 更新进度
                state["progress"].append(
                    {
                        "step": "technical_analyzer",
                        "status": "success",
                        "message": f"技术面分析完成，共分析 {len(factors)} 个因子",
                        "data": technical_analysis["summary"],
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            else:
                state["error"] = result.get("error", "技术面分析失败")
                state["progress"].append(
                    {
                        "step": "technical_analyzer",
                        "status": "error",
                        "message": f"技术面分析失败: {state['error']}",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            return state

        except Exception as e:
            state["error"] = str(e)
            state["progress"].append(
                {
                    "step": "technical_analyzer",
                    "status": "error",
                    "message": f"技术面分析异常: {str(e)}",
                    "timestamp": datetime.now().isoformat(),
                }
            )
            return state

    def _qlib_analysis_node(self, state: AgentState) -> AgentState:
        """Qlib因子分析节点"""
        try:
            symbol = state["symbol"]

            # 更新进度
            state["progress"].append(
                {
                    "step": "qlib_analyzer",
                    "status": "running",
                    "message": "正在进行Qlib因子分析...",
                    "timestamp": datetime.now().isoformat(),
                }
            )
            state["current_step"] = "qlib_analyzer"

            # 获取Qlib因子
            result = stock_service.get_qlib_factors_for_agent(symbol)

            if result["success"]:
                factors = result["data"]

                # 转换为结构化数据
                qlib_analysis = {"factors": [], "summary": {"total_factors": len(factors)}}

                for factor in factors:
                    factor_dict = {
                        "name": factor.name,
                        "key": factor.key,
                        "status": factor.status,
                        "value": None,
                    }

                    # 尝试从status中提取数值
                    try:
                        if (
                            factor.status
                            and factor.status.replace(".", "").replace("-", "").isdigit()
                        ):
                            factor_dict["value"] = float(factor.status)
                    except:
                        pass

                    qlib_analysis["factors"].append(factor_dict)

                state["qlib_data"] = {"analysis": qlib_analysis, "raw_factors": factors}

                # 更新进度
                state["progress"].append(
                    {
                        "step": "qlib_analyzer",
                        "status": "success",
                        "message": f"Qlib因子分析完成，共计算 {len(factors)} 个因子",
                        "data": qlib_analysis["summary"],
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            else:
                state["error"] = result.get("error", "Qlib因子分析失败")
                state["progress"].append(
                    {
                        "step": "qlib_analyzer",
                        "status": "error",
                        "message": f"Qlib因子分析失败: {state['error']}",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            return state

        except Exception as e:
            state["error"] = str(e)
            state["progress"].append(
                {
                    "step": "qlib_analyzer",
                    "status": "error",
                    "message": f"Qlib因子分析异常: {str(e)}",
                    "timestamp": datetime.now().isoformat(),
                }
            )
            return state

    def _decision_maker_node(self, state: AgentState) -> AgentState:
        """决策节点 - 汇总所有分析结果，生成最终投资建议"""
        try:
            # 更新进度
            state["progress"].append(
                {
                    "step": "decision_maker",
                    "status": "running",
                    "message": "正在生成投资决策建议...",
                    "timestamp": datetime.now().isoformat(),
                }
            )
            state["current_step"] = "decision_maker"

            # 汇总所有分析结果
            fundamental_data = state.get("fundamental_data")
            technical_data = state.get("technical_data")
            qlib_data = state.get("qlib_data")

            analysis_summary = {
                "symbol": state["symbol"],
                "timestamp": datetime.now().isoformat(),
                "fundamental": fundamental_data.get("analysis") or {} if fundamental_data else {},
                "technical": technical_data.get("analysis") or {} if technical_data else {},
                "qlib": qlib_data.get("analysis") or {} if qlib_data else {},
                "overall_score": self._calculate_overall_score(state),
                "recommendation": self._generate_recommendation(state),
            }

            state["analysis_result"] = analysis_summary

            # 更新进度
            state["progress"].append(
                {
                    "step": "decision_maker",
                    "status": "success",
                    "message": "投资决策分析完成",
                    "data": {
                        "overall_score": analysis_summary["overall_score"],
                        "recommendation": analysis_summary["recommendation"]["action"],
                    },
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return state

        except Exception as e:
            state["error"] = str(e)
            state["progress"].append(
                {
                    "step": "decision_maker",
                    "status": "error",
                    "message": f"决策分析异常: {str(e)}",
                    "timestamp": datetime.now().isoformat(),
                }
            )
            return state

    def _calculate_overall_score(self, state: AgentState) -> Dict[str, Any]:
        """计算综合评分"""
        score = {"fundamental_score": 0, "technical_score": 0, "total_score": 0, "max_score": 100}

        # 基本面评分 (40%权重)
        fundamental_state_data = state.get("fundamental_data")
        fundamental_data = (
            fundamental_state_data.get("analysis") or {} if fundamental_state_data else {}
        )
        if fundamental_data:
            summary = fundamental_data.get("summary") or {}
            total_factors = summary.get("total_factors", 0)
            if total_factors > 0:
                bullish_ratio = summary.get("bullish_count", 0) / total_factors
                score["fundamental_score"] = int(bullish_ratio * 40)

        # 技术面评分 (60%权重)
        technical_state_data = state.get("technical_data")
        technical_data = technical_state_data.get("analysis") or {} if technical_state_data else {}
        if technical_data:
            summary = technical_data.get("summary") or {}
            total_factors = summary.get("total_factors", 0)
            if total_factors > 0:
                bullish_ratio = summary.get("bullish_count", 0) / total_factors
                score["technical_score"] = int(bullish_ratio * 60)

        score["total_score"] = score["fundamental_score"] + score["technical_score"]

        return score

    def _generate_recommendation(self, state: AgentState) -> Dict[str, Any]:
        """生成投资建议"""
        score = self._calculate_overall_score(state)
        total_score = score["total_score"]

        if total_score >= 70:
            return {"action": "买入", "confidence": "高", "reason": "多维度分析显示强烈的买入信号"}
        elif total_score >= 50:
            return {
                "action": "持有",
                "confidence": "中等",
                "reason": "分析结果中性偏积极，建议持有观察",
            }
        elif total_score >= 30:
            return {"action": "观望", "confidence": "中等", "reason": "存在一定风险，建议观望"}
        else:
            return {"action": "卖出", "confidence": "高", "reason": "多维度分析显示强烈的卖出信号"}

    def run_analysis(self, symbol: str):
        """运行股票分析工作流"""
        # 初始化状态
        initial_state = AgentState(
            symbol=symbol,
            messages=[],
            current_step="",
            error=None,
            fundamental_data=None,
            technical_data=None,
            qlib_data=None,
            analysis_result=None,
            progress=[],
        )

        # 执行工作流
        for output in self.graph.stream(initial_state):
            yield output

    def add_custom_node(self, node_name: str, node_func):
        """添加自定义节点（扩展性）"""
        self.graph.add_node(node_name, node_func)
        return self

    def insert_node_after(self, existing_node: str, new_node: str, node_func):
        """在指定节点后插入新节点"""
        _ = existing_node  # 暂时未使用，预留扩展
        self.graph.add_node(new_node, node_func)
        # 需要重建edges，这里简化处理
        return self
