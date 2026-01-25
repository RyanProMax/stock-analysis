"""
TechnicalAgent Prompts - 技术面分析提示词
"""

from typing import Optional

from ...core import FactorAnalysis


TECHNICAL_SYSTEM_MESSAGE = """
你是一位专注于技术面分析的股票分析师。

你的任务是**直接解读原始技术数据(raw_data)**，进行全面的技术面分析。

## 分析要求

### 1. 自动识别指标
从原始数据中自动识别并分析以下维度的指标（字段名可能因数据源不同而有差异，请根据语义理解）：

**趋势指标**
- MA5/MA10/MA20/MA60：均线排列和金叉死叉
- MACD：DIF、DEA、柱状图的变化
- EMA：短期和中期趋势
- 趋势线支撑和压力

**动量指标**
- RSI：超买超卖判断（>70超买，<30超卖）
- KDJ：K、D、J值的位置和交叉（>90超买，<10超卖）
- WR：威廉指标判断
- CCI：顺势指标

**成交量指标**
- 成交量变化：放量缩量与价格关系
- VR：成交量变异率
- OBV：能量潮指标

**波动率指标**
- 布林带：价格波动范围和突破信号
- ATR：真实波动幅度

### 2. 技术分析原则
- 趋势优先：大趋势决定操作方向
- 量价配合：放量突破更可信
- 指标共振：多指标同向信号更可靠
- 支撑阻力：关键价位是买卖点

## 输出格式

使用Markdown格式，包含：
1. **核心指标分析**：列出从raw_data中提取的关键指标及数值，并列出重要的看涨或看跌信号
2. **技术趋势判断**：上升/下降/震荡，及理由
3. **技术面投资建议**：基于技术面的买入/持有/卖出/观望建议
4. **支撑/阻力位**：关键价位判断（如有数据支持）

请确保分析**仅基于技术面数据**，不要提及基本面因素。
"""


def _format_raw_data(raw_data: dict) -> str:
    """格式化原始技术数据为LLM可读的形式"""
    lines = []

    # 遍历raw_data的各个数据块
    for section_name, section_data in raw_data.items():
        lines.append(f"\n### {section_name}")

        if isinstance(section_data, dict):
            # 将字典按key排序后输出，便于LLM阅读
            for key, value in sorted(section_data.items()):
                # 跳过None值和空字符串
                if value is None or value == "" or value == "-":
                    continue
                lines.append(f"- {key}: {value}")
        else:
            lines.append(f"{section_data}")

    return "\n".join(lines)


def build_technical_prompt(
    symbol: str,
    stock_name: str = "",
    technical: Optional[FactorAnalysis] = None,
) -> str:
    """构建技术面分析提示词"""
    prompt_parts = []

    # 股票基本信息
    stock_info = f"## 股票信息\n- 代码: {symbol}"
    if stock_name:
        stock_info += f"\n- 名称: {stock_name}"
    prompt_parts.append(stock_info)

    # 原始技术数据
    assert technical is not None and technical.raw_data is not None
    prompt_parts.append("\n## 原始技术数据 (raw_data)")
    prompt_parts.append("以下是完整的原始技术数据，请直接解读并分析：")
    prompt_parts.append(_format_raw_data(technical.raw_data))

    # 任务指令
    prompt_parts.append("\n## 分析任务")
    prompt_parts.append("请基于以上原始技术数据，提取并分析所有有价值的技术指标，")
    prompt_parts.append("给出专业的技术面分析报告。")

    return "\n".join(prompt_parts)
