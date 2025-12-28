"""
Agent控制器 - 提供流式股票分析接口
"""

import json
from typing import Optional
from fastapi import APIRouter, Query
from sse_starlette.sse import EventSourceResponse

from ..agent.stock_analysis_agent import StockAnalysisAgent

router = APIRouter()
agent = StockAnalysisAgent()


@router.get("/analyze")
async def analyze_stock_stream(
    symbol: str = Query(..., description="股票代码", example="NVDA"),
    refresh: Optional[bool] = Query(False, description="是否强制刷新缓存"),
):
    """
    流式股票分析接口

    使用Server-Sent Events (SSE)实时返回分析进度
    """
    symbol = symbol.upper()

    async def generate():
        try:
            # 发送开始事件
            yield {
                "event": "start",
                "data": json.dumps(
                    {
                        "type": "start",
                        "message": f"开始分析股票: {symbol}",
                        "symbol": symbol,
                    },
                    ensure_ascii=False,
                ),
            }

            # 用于去重的集合，记录已发送的进度事件
            sent_progress = set()

            # 运行分析工作流
            async for output in agent.run_analysis(symbol):
                # 提取当前节点的进度信息
                for _, node_state in output.items():
                    if "progress" in node_state:
                        for progress in node_state["progress"]:
                            # 创建唯一的进度标识
                            progress_id = (
                                progress["step"],
                                progress["status"],
                                progress["timestamp"],
                            )

                            # 只发送未重复的进度事件
                            if progress_id not in sent_progress:
                                sent_progress.add(progress_id)
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
