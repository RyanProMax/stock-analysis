"""
Agent控制器 - 提供流式股票分析接口
"""

import json
import asyncio
from typing import Dict, Any, AsyncGenerator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from ..agent.stock_analysis_agent import StockAnalysisAgent
from ..controller.schemas import StandardResponse

router = APIRouter()
agent = StockAnalysisAgent()


@router.get("/{symbol}/analyze/stream")
async def analyze_stock_stream(symbol: str):
    """
    流式股票分析接口

    使用Server-Sent Events (SSE)实时返回分析进度
    """

    async def generate():
        try:
            # 发送开始事件
            yield {
                "event": "start",
                "data": json.dumps(
                    {"type": "start", "message": f"开始分析股票: {symbol}", "symbol": symbol},
                    ensure_ascii=False,
                ),
            }

            # 运行分析工作流
            async for output in agent.run_analysis(symbol):
                # 提取当前节点的进度信息
                for node_name, node_state in output.items():
                    if "progress" in node_state:
                        for progress in node_state["progress"]:
                            # 发送进度事件
                            yield {
                                "event": "progress",
                                "data": json.dumps(
                                    {
                                        "type": "progress",
                                        "step": progress["step"],
                                        "status": progress["status"],
                                        "message": progress["message"],
                                        "data": progress.get("data"),
                                        "timestamp": progress["timestamp"],
                                    },
                                    ensure_ascii=False,
                                ),
                            }

                    # 检查是否有错误
                    if "error" in node_state and node_state["error"]:
                        yield {
                            "event": "error",
                            "data": json.dumps(
                                {
                                    "type": "error",
                                    "message": node_state["error"],
                                    "step": node_state.get("current_step", "unknown"),
                                },
                                ensure_ascii=False,
                            ),
                        }
                        return

                    # 如果是最终结果
                    if "analysis_result" in node_state and node_state["analysis_result"]:
                        yield {
                            "event": "complete",
                            "data": json.dumps(
                                {
                                    "type": "complete",
                                    "result": node_state["analysis_result"],
                                    "message": "股票分析完成",
                                },
                                ensure_ascii=False,
                            ),
                        }
                        return

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps(
                    {"type": "error", "message": f"分析过程中发生错误: {str(e)}"},
                    ensure_ascii=False,
                ),
            }

    return EventSourceResponse(generate())


@router.get("/{symbol}/analyze")
async def analyze_stock(symbol: str):
    """
    非流式股票分析接口（兼容原有接口）

    返回完整的分析结果
    """
    try:
        # 收集所有分析结果
        final_result = None
        error_message = None

        async for output in agent.run_analysis(symbol):
            for node_name, node_state in output.items():
                if "error" in node_state and node_state["error"]:
                    error_message = node_state["error"]
                    break

                if "analysis_result" in node_state and node_state["analysis_result"]:
                    final_result = node_state["analysis_result"]
                    break

            if error_message:
                break

        if error_message:
            raise HTTPException(status_code=500, detail=error_message)

        if not final_result:
            raise HTTPException(status_code=500, detail="分析未返回结果")

        return StandardResponse(status_code=200, data=final_result, err_msg=None)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


# 添加一个WebSocket接口作为备选方案（可选）
@router.websocket("/{symbol}/analyze/ws")
async def analyze_stock_websocket(websocket, symbol: str):
    """
    WebSocket股票分析接口（可选实现）
    """
    await websocket.accept()

    try:
        # 发送开始消息
        await websocket.send_json(
            {"type": "start", "message": f"开始分析股票: {symbol}", "symbol": symbol}
        )

        # 运行分析
        async for output in agent.run_analysis(symbol):
            for node_name, node_state in output.items():
                if "progress" in node_state:
                    for progress in node_state["progress"]:
                        await websocket.send_json(
                            {
                                "type": "progress",
                                "step": progress["step"],
                                "status": progress["status"],
                                "message": progress["message"],
                                "data": progress.get("data"),
                                "timestamp": progress["timestamp"],
                            }
                        )

                if "error" in node_state and node_state["error"]:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": node_state["error"],
                            "step": node_state.get("current_step", "unknown"),
                        }
                    )
                    await websocket.close()
                    return

                if "analysis_result" in node_state and node_state["analysis_result"]:
                    await websocket.send_json(
                        {
                            "type": "complete",
                            "result": node_state["analysis_result"],
                            "message": "股票分析完成",
                        }
                    )
                    await websocket.close()
                    return

    except Exception as e:
        await websocket.send_json({"type": "error", "message": f"WebSocket连接错误: {str(e)}"})
        await websocket.close()
