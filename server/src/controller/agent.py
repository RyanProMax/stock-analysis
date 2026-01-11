"""
Agent控制器 - 流式股票分析接口 (Multi-Agent 架构)
"""

import json
import asyncio
from typing import Optional, Any
from fastapi import APIRouter, Query
from sse_starlette.sse import EventSourceResponse

from ..agents.coordinator import MultiAgentSystem
from ..agents.llm import LLMManager

router = APIRouter()
llm_manager = LLMManager()


def send_event(event_type: str, data: dict) -> dict:
    """创建 SSE 事件"""
    return {"event": event_type, "data": json.dumps(data, ensure_ascii=False)}


def send_progress(step: str, status: str, message: str, data: Optional[dict] = None) -> dict:
    """创建进度事件"""
    event_data: dict[str, Any] = {
        "type": "progress",
        "step": step,
        "status": status,
        "message": message,
    }
    if data:
        event_data["data"] = data
    return send_event("progress", event_data)


@router.get("/analyze")
async def analyze_stock_stream(
    symbol: str = Query(..., description="股票代码", example="NVDA"),
    refresh: Optional[bool] = Query(False, description="是否强制刷新缓存"),
    max_tokens: Optional[int] = Query(None, description="LLM 最大生成token数，默认不限制"),
):
    """
    流式股票分析接口 (Multi-Agent 架构)

    分析流程：
    1. DataAgent 获取股票数据（价格、基本面、技术面）
    2. FundamentalAgent 基本面分析（独立 LLM）
    3. TechnicalAgent 技术面分析（独立 LLM）
    4. CoordinatorAgent 综合分析并给出最终投资建议（流式输出，包含思考过程）

    子 Agents 并行执行，提升分析速度。
    """
    symbol = symbol.upper()
    use_llm = llm_manager.is_available
    system = MultiAgentSystem(llm_manager)

    async def generate():
        try:
            yield send_event("start", {"type": "start", "symbol": symbol})

            # 使用新的流式接口，实时接收进度事件
            state = None
            stream_gen = None

            async for (
                event_type,
                event_state,
                event_stream_gen,
                event_message,
            ) in system.analyze_stream(symbol):
                state = event_state
                if event_stream_gen is not None:
                    stream_gen = event_stream_gen

                # 解析事件类型
                if event_type == "error":
                    yield send_event(
                        "error",
                        {
                            "type": "error",
                            "message": event_message or state.errors.get("DataAgent", "分析错误"),
                        },
                    )
                    return

                # 解析 step:status 格式的事件，透传消息
                if ":" in event_type:
                    step, status = event_type.split(":", 1)
                    message = event_message or status
                    yield send_progress(step, status, message)

            # 检查是否有数据获取错误
            if state and state.has_error("DataAgent"):
                yield send_event(
                    "error",
                    {"type": "error", "message": state.errors["DataAgent"]},
                )
                return

            # 发送因子数据（用于前端展示）
            yield send_progress(
                "fundamental_analyzer",
                "success",
                "基本面因子",
                {"factors": state.fundamental_factors or [] if state else []},
            )
            yield send_progress(
                "technical_analyzer",
                "success",
                "技术面因子",
                {"factors": state.technical_factors or [] if state else []},
            )

            # 流式输出综合分析结果
            yield send_progress("coordinator", "running", "正在生成综合报告...")

            full_response = ""
            thinking_process = ""

            if use_llm and stream_gen is not None:
                async for chunk, thinking_type in stream_gen:
                    if thinking_type == "thinking":
                        # 思考过程，单独发送
                        thinking_process += chunk
                        yield send_event(
                            "thinking",
                            {
                                "type": "thinking",
                                "step": "coordinator",
                                "content": chunk,
                            },
                        )
                    else:
                        # 正常内容
                        full_response += chunk
                        yield send_event(
                            "streaming",
                            {
                                "type": "streaming",
                                "step": "coordinator",
                                "content": chunk,
                            },
                        )
                    await asyncio.sleep(0)

                decision = {
                    "action": "分析完成",
                    "analysis": full_response,
                    "thinking": thinking_process,
                }
            else:
                # 如果没有 LLM，返回因子数据
                fundamental_text = (
                    state.fundamental_analysis or "基本面分析: " + str(state.fundamental_factors)
                    if state
                    else "基本面分析: 无数据"
                )
                technical_text = (
                    state.technical_analysis or "技术面分析: " + str(state.technical_factors)
                    if state
                    else "技术面分析: 无数据"
                )
                decision = {
                    "action": "LLM未配置",
                    "analysis": f"{fundamental_text}\n\n{technical_text}",
                }

            # 更新最后一个节点状态为完成
            execution_time = state.execution_times.get("CoordinatorAgent", 0) if state else 0
            yield send_progress(
                "coordinator", "success", "分析完成", {"execution_time": execution_time}
            )

            # 完成
            yield send_event(
                "complete",
                {
                    "type": "complete",
                    "result": {
                        "symbol": symbol,
                        "stock_name": state.stock_name if state else "",
                        "decision": decision,
                        "execution_times": state.execution_times if state else {},
                    },
                },
            )

        except Exception as e:
            import traceback

            traceback.print_exc()
            yield send_event("error", {"type": "error", "message": f"分析错误: {str(e)}"})

    return EventSourceResponse(generate(), media_type="text/event-stream")
