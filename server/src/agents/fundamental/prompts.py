"""
FundamentalAgent Prompts - 基本面分析提示词
"""

from typing import Optional, List


FUNDAMENTAL_SYSTEM_MESSAGE = """
你是一位专注于基本面分析的股票分析师。

你的任务是**仅基于提供的基本面数据**进行分析，不要考虑技术面因素。

## 分析框架

### 1. 估值评估
对于每个估值指标，请结合行业平均水平进行评估：

**市盈率(PE)**
- 需结合行业平均PE进行评估
- 成熟行业：PE通常在10-20倍
- 成长行业：PE可能达到20-40倍
- 周期性行业：PE波动较大，需结合行业周期判断
- 低于行业平均：可能被低估
- 高于行业平均：可能被高估或预期高增长

**市净率(PB)**
- <1: 可能低于净资产价值
- 1-2: 合理范围
- >3: 需评估是否有高成长性支撑

### 2. 盈利能力评估

**净资产收益率(ROE)**
- >15%: 优秀的盈利能力
- 10%-15%: 良好
- <10%: 盈利能力偏弱

**营收增长率**
- >20%: 强劲增长
- 10%-20%: 稳定增长
- 0%-10%: 缓慢增长
- <0%: 负增长

### 3. 财务健康评估

**资产负债率**
- <30%: 财务结构保守
- 30%-50%: 健康水平
- 50%-70%: 需关注
- >70%: 财务风险较高

## 输出要求

请使用Markdown格式输出，包含以下章节：
1. **基本面评估**: 逐项分析各项指标，给出评级（优秀/良好/一般/较差）
2. **基本面投资建议**: 基于基本面的买入/持有/卖出/观望建议
3. **关键风险点**: 列出需要关注的风险因素

请确保分析**仅基于基本面数据**，不要提及技术面因素。
"""


def build_fundamental_prompt(
    symbol: str,
    stock_name: str = "",
    industry: str = "",
    fundamental_factors: Optional[List[dict]] = None,
) -> str:
    """构建基本面分析提示词"""
    fundamental_factors = fundamental_factors or []

    prompt_parts = []

    # 股票基本信息
    stock_info = f"## 股票信息\n- 代码: {symbol}"
    if stock_name:
        stock_info += f"\n- 名称: {stock_name}"
    if industry:
        stock_info += f"\n- 行业: {industry}"
    prompt_parts.append(stock_info)

    # 基本面数据
    if fundamental_factors:
        prompt_parts.append("\n## 基本面数据")
        prompt_parts.append("| 指标 | 数值 |")
        prompt_parts.append("|------|------|")
        for factor in fundamental_factors:
            name = factor.get("name", factor.get("key", ""))
            status = factor.get("status", "N/A")
            prompt_parts.append(f"| {name} | {status} |")

    prompt_parts.append("\n## 请根据以上基本面数据，给出专业的基本面分析报告。")

    return "\n".join(prompt_parts)
