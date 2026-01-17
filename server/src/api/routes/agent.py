"""
Agent控制器 - 流式股票分析接口 (Multi-Agent 架构)
"""

import json
import asyncio
from typing import Optional, Any
from fastapi import APIRouter, Query
from sse_starlette.sse import EventSourceResponse

from ...agents.coordinator import MultiAgentSystem
from ...agents.llm import LLMManager

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
    1. FundamentalAgent + TechnicalAgent 并行分析（各自负责获取数据）
    2. CoordinatorAgent 综合分析并给出最终投资建议（流式输出���包含思考过程）

    子 Agents 并行执行，提升分析速度。
    """
    symbol = symbol.upper()
    use_llm = llm_manager.is_available
    system = MultiAgentSystem(llm_manager)

    async def generate():
        yield send_event("start", {"type": "start", "symbol": symbol})

        # 使用新的流式接口，实时接收进度事件
        state = None
        coordinator_full_response = ""
        coordinator_thinking = ""

        async for (
            event_type,
            event_state,
            event_stream_chunk,
            event_message,
            event_data,
        ) in system.analyze_stream(symbol):

            state = event_state

            # 解析事件类型
            if event_type == "error":
                yield send_event(
                    "error",
                    {
                        "type": "error",
                        "message": event_message or "分析错误",
                    },
                )
                return

            # 处理子 Agent 的流式输出 (event_stream_chunk 是 (chunk, thinking_type) 元组)
            if event_stream_chunk is not None:
                # 检查是否为正确的格式
                if isinstance(event_stream_chunk, tuple) and len(event_stream_chunk) == 2:
                    chunk, thinking_type = event_stream_chunk
                    step_key = event_type.split(":")[0] if ":" in event_type else "unknown"

                    # 累积 coordinator 的内容用于最终结果
                    if step_key == "coordinator":
                        if thinking_type == "thinking":
                            coordinator_thinking += chunk
                        else:
                            coordinator_full_response += chunk

                    if thinking_type == "thinking":
                        yield send_event(
                            "thinking",
                            {
                                "type": "thinking",
                                "step": step_key,
                                "content": chunk,
                            },
                        )
                    else:
                        yield send_event(
                            "streaming",
                            {
                                "type": "streaming",
                                "step": step_key,
                                "content": chunk,
                            },
                        )
                    await asyncio.sleep(0)
                    continue
                else:
                    # event_stream_chunk 格式不正确，可能是旧版本返回的生成器
                    # 跳过并记录警告
                    import logging

                    logging.warning(
                        f"Invalid event_stream_chunk format: {type(event_stream_chunk)}"
                    )
                    continue

            # 解析 step:status 格式的事件，透传消息和数据
            if ":" in event_type:
                step, status = event_type.split(":", 1)
                message = event_message or status
                # 如果有 data 参数，将其包装为 factors 格式
                data = None
                if event_data is not None:
                    data = {"factors": event_data}
                yield send_progress(step, status, message, data)

                # 收集 coordinator 的完整响应用于最终结果
                if step == "coordinator" and status == "streaming":
                    # 由流式事件处理，这里不需要额外处理
                    pass

        # 检查是否所有分析都失败
        if state and state.has_error("FundamentalAgent") and state.has_error("TechnicalAgent"):
            yield send_event(
                "error",
                {"type": "error", "message": "分析失败"},
            )
            return

        # 构建最终决策
        if use_llm:
            decision = {
                "action": "分析完成",
                "analysis": coordinator_full_response
                or (state.coordinator_analysis if state else "")
                or "",
                "thinking": coordinator_thinking or (state.thinking_process if state else "") or "",
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
            "coordinator",
            "completed",
            "分析完成",
            {"execution_time": execution_time},
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

    return EventSourceResponse(generate(), media_type="text/event-stream")
