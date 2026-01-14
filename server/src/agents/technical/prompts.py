"""
TechnicalAgent Prompts - 技术面分析提示词
"""

from typing import Optional, List


TECHNICAL_SYSTEM_MESSAGE = """
你是一位专注于技术面分析的股票分析师。

你的任务是**仅基于提供的技术面数据**进行分析，不要考虑基本面因素。

请使用 <thinking> 和 </thinking> 标签包裹你的分析推理过程。

## 分析框架

### 1. 趋势分析
- **均线系统**: MA5/MA20/MA60 的排列和金叉死叉
- **MACD**: 趋势强度和方向变化
- **EMA**: 短期和中期趋势

### 2. 动量分析
- **RSI**: 超买超卖判断（>70超买，<30超卖）
- **KDJ**: J值判断（>90超买，<10超卖）
- **WR**: 威廉指标判断

### 3. 成交量分析
- **成交量变化**: 放量缩量与价格关系
- **VR**: 成交量变异率

### 4. 波动率分析
- **布林带**: 价格波动范围和突破信号
- **ATR**: 波动幅度

## 输出要求

请使用Markdown格式输出，包含以下章节：
1. **技术趋势判断**: 上升/下降/震荡，及理由
2. **关键技术信号**: 列出重要的看涨或看跌信号
3. **技术面投资建议**: 基于技术面的买入/持有/卖出/观望建议
4. **支撑/阻力位**: 关键价位判断（如有数据支持）

请确保分析**仅基于技术面数据**，不要提及基本面因素。
"""


def build_technical_prompt(
    symbol: str,
    stock_name: str = "",
    technical_factors: Optional[List[dict]] = None,
) -> str:
    """构建技术面分析提示词"""
    technical_factors = technical_factors or []

    prompt_parts = []

    # 股票基本信息
    stock_info = f"## 股票信息\n- 代码: {symbol}"
    if stock_name:
        stock_info += f"\n- 名称: {stock_name}"
    prompt_parts.append(stock_info)

    # 技术面数据
    if technical_factors:
        prompt_parts.append("\n## 技术面数据")
        for factor in technical_factors:
            name = factor.get("name", factor.get("key", ""))
            status = factor.get("status", "N/A")
            bullish = factor.get("bullish_signals", [])
            bearish = factor.get("bearish_signals", [])

            prompt_parts.append(f"\n### {name}")
            prompt_parts.append(f"- 状态: {status}")
            if bullish:
                prompt_parts.append("- 看涨信号:")
                for signal in bullish:
                    prompt_parts.append(f"  - {signal}")
            if bearish:
                prompt_parts.append("- 看跌信号:")
                for signal in bearish:
                    prompt_parts.append(f"  - {signal}")

    prompt_parts.append("\n## 请根据以上技术面数据，给出专业的技术面分析报告。")

    return "\n".join(prompt_parts)
