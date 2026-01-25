"""
FundamentalAgent Prompts - 基本面分析提示词
"""

from typing import Optional

from ...core import FactorAnalysis


FUNDAMENTAL_SYSTEM_MESSAGE = """
你是一位专注于基本面分析的股票分析师。

你的任务是**直接解读原始财务数据(raw_data)**，进行全面的基本面分析。

## 分析要求

### 1. 自动识别指标
从原始数据中自动识别并分析以下维度的指标（字段名可能因数据源不同而有差异，请根据语义理解）：

**估值指标**
- 市盈率(PE)、市净率(PB)、市销率(PS)
- 企业价值倍数(EV/EBITDA)

**盈利能力**
- 净资产收益率(ROE)、总资产收益率(ROA)
- 毛利率、净利率、营业利润率
- EBITDA利润率

**成长性**
- 营收增长率、净利润增长率
- EPS增长率、ROE增长率

**财务健康**
- 资产负债率、权益乘数
- 流动比率、速动比率
- 利息保障倍数、现金比率

**运营效率**
- 存货周转率、应收账款周转率
- 总资产周转率

**现金流**
- 经营现金流、自由现金流
- 经营现金流/净利润

### 2. 行业对比评估
结合行业特点评估各项指标：
- 周期性行业：关注PB、行业周期位置
- 成长行业：可容忍较高PE，重点关注增长率
- 成熟行业：关注分红、现金流

### 3. 综合判断
- 识别公司的竞争优势（护城河）
- 评估财务风险
- 判断估值合理性

## 输出格式

使用Markdown格式，包含：
1. **核心指标分析**：列出从raw_data中提取的关键指标及数值
2. **多维度评估**：估值/盈利能力/成长性/财务健康度
3. **投资建议**：买入/持有/卖出/观望，并说明理由
4. **风险提示**：需要关注的风险因素
"""


def _format_raw_data(raw_data: dict) -> str:
    """格式化原始财务数据为LLM可读的形式"""
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


def build_fundamental_prompt(
    symbol: str,
    stock_name: str = "",
    industry: str = "",
    fundamental: Optional[FactorAnalysis] = None,
) -> str:
    """构建基本面分析提示词"""
    prompt_parts = []

    # 股票基本信息
    stock_info = f"## 股票信息\n- 代码: {symbol}"
    if stock_name:
        stock_info += f"\n- 名称: {stock_name}"
    if industry:
        stock_info += f"\n- 行业: {industry}"
    prompt_parts.append(stock_info)

    # 原始财务数据
    assert fundamental is not None and fundamental.raw_data is not None
    prompt_parts.append("\n## 原始财务数据 (raw_data)")
    prompt_parts.append("以下是完整的原始财务数据，请直接解读并分析：")
    prompt_parts.append(_format_raw_data(fundamental.raw_data))

    # 任务指令
    prompt_parts.append("\n## 分析任务")
    prompt_parts.append("请基于以上原始财务数据，提取并分析所有有价值的基本面指标，")
    prompt_parts.append("给出专业的投资建议和风险提示。")

    return "\n".join(prompt_parts)
