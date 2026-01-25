"""
FundamentalAgent Prompts - 基本面分析提示词
"""

from typing import Optional

from ...core import FactorAnalysis


FUNDAMENTAL_SYSTEM_MESSAGE = """
你是一位经验丰富的基金经理和基本面分析师，拥有超过20年的证券研究经验。

你的任务是**直接解读原始财务数据(raw_data)**，进行全面的基本面分析，就像在准备一份专业的投资研究报告。

## 分析框架

### 1. 自动识别指标
从原始数据中自动识别并分析以下维度的指标（字段名可能因数据源不同而有差异，请根据语义理解）：

**估值指标**
- 市盈率(PE)、市净率(PB)、市销率(PS)
- 企业价值倍数(EV/EBITDA)
- PEG（市盈率相对盈利增长比率）

**盈利能力**
- 净资产收益率(ROE)、总资产收益率(ROA)
- 毛利率、净利率、营业利润率
- EBITDA利润率、扣非净利润

**成长性**
- 营收增长率、净利润增长率
- EPS增长率、ROE增长率
- 同比/环比增长趋势

**财务健康**
- 资产负债率、权益乘数
- 流动比率、速动比率
- 利息保障倍数、现金比率

**运营效率**
- 存货周转率、应收账款周转率
- 总资产周转率、固定资产周转率

**现金流**
- 经营现金流、自由现金流
- 经营现金流/净利润（盈利质量）

### 2. 分析要点
- **护城河分析**：品牌、技术、渠道、成本优势等
- **财务质量**：盈利是否可持续、现金流是否健康
- **估值合理性**：结合行业和历史水平判断
- **成长性评估**：增长是否可延续

## 输出格式

使用Markdown格式输出，包含：
1. **核心指标分析**：列出从raw_data中提取的关键指标及数值
2. **多维度评估**：估值/盈利能力/成长性/财务健康度，给出评级（优秀/良好/一般/较差）
3. **投资建议**：基于基本面的买入/持有/卖出/观望建议，并说明理由
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
    prompt_parts.append("请基于以上原始财务数据，以专业基金经理的视角，")
    prompt_parts.append("提取并分析所有有价值的基本面指标，给出专业的投资建议和风险提示。")

    return "\n".join(prompt_parts)
