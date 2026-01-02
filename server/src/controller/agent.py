"""
Agent控制器 - 流式股票分析接口
"""

import json
import asyncio
from typing import Optional, List, Any
from fastapi import APIRouter, Query
from sse_starlette.sse import EventSourceResponse

from ..service.stock_service import stock_service
from ..agent import prompts
from ..agent.llm import DEFAULT_TEMPERATURE, LLMManager
from openai.types.chat import ChatCompletionMessageParam

router = APIRouter()
llm_manager = LLMManager()


def convert_factors_to_dict(factors) -> List[dict]:
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


def convert_qlib_factors_to_dict(factors) -> List[dict]:
    """将Qlib因子转换为字典"""
    result = []
    for factor in factors or []:
        if hasattr(factor, "name"):
            result.append(
                {
                    "name": getattr(factor, "name", ""),
                    "key": getattr(factor, "key", ""),
                    "value": getattr(factor, "status", ""),
                }
            )
    return result


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
    """流式股票分析接口"""
    symbol = symbol.upper()
    use_llm = llm_manager.is_available

    async def generate():
        try:
            yield send_event("start", {"type": "start", "symbol": symbol})

            # 1. 数据获取
            yield send_progress("data_fetcher", "running", f"正在获取 {symbol} 数据...")
            report = stock_service.analyze_symbol(symbol)
            if not report:
                yield send_event("error", {"type": "error", "message": "无法获取数据"})
                return
            yield send_progress("data_fetcher", "success", f"成功获取 {symbol} 数据")

            # 准备因子数据
            fundamental_factors = convert_factors_to_dict(report.fundamental_factors)
            technical_factors = convert_factors_to_dict(report.technical_factors)

            # 2. 基本面分析
            yield send_progress("fundamental_analyzer", "running", "基本面分析中...")
            await asyncio.sleep(0.05)
            yield send_progress(
                "fundamental_analyzer",
                "success",
                "基本面分析完成",
                {"factors": fundamental_factors},
            )

            # 3. 技术面分析
            yield send_progress("technical_analyzer", "running", "技术面分析中...")
            await asyncio.sleep(0.05)
            yield send_progress(
                "technical_analyzer",
                "success",
                "技术面分析完成",
                {"factors": technical_factors},
            )

            # 4. 决策分析（流式 LLM）
            yield send_progress("decision_maker", "running", "正在生成分析报告...")

            llm_data = {
                "symbol": symbol,
                "fundamental_factors": fundamental_factors,
                "technical_factors": technical_factors,
            }

            prompt = json.dumps(llm_data, indent=2, ensure_ascii=False)

            full_response = ""
            if use_llm:
                messages: List[ChatCompletionMessageParam] = [
                    {"role": "system", "content": prompts.DECISION_SYSTEM_MESSAGE},
                    {
                        "role": "user",
                        "content": f"请分析股票数据并给出建议：\n\n{prompt}",
                    },
                ]

                async for chunk in llm_manager.chat_completion_stream(
                    messages=messages,
                    temperature=DEFAULT_TEMPERATURE,
                    max_tokens=max_tokens,
                ):
                    full_response += chunk
                    yield send_event(
                        "streaming",
                        {
                            "type": "streaming",
                            "step": "decision_maker",
                            "content": chunk,
                        },
                    )
                    await asyncio.sleep(0)

                decision = {"action": "分析完成", "analysis": full_response}
            else:
                decision = {"action": "无LLM", "analysis": "LLM未配置"}

            # 更新最后一个节点状态为完成
            yield send_progress("decision_maker", "success", "分析完成")

            # 5. 完成
            yield send_event(
                "complete",
                {
                    "type": "complete",
                    "result": {"symbol": symbol, "decision": decision},
                },
            )

        except Exception as e:
            import traceback

            traceback.print_exc()
            yield send_event("error", {"type": "error", "message": f"分析错误: {str(e)}"})

    return EventSourceResponse(generate(), media_type="text/event-stream")
