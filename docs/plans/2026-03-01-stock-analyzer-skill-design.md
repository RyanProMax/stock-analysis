# 股票分析 Skill 设计文档

**日期**: 2026-03-01
**主题**: 外部 API 股票分析报告生成 Skill

## 1. 需求概述

创建一个 Claude Code Skill，功能如下：
- 请求指定外部股票分析 API
- 获取股票指标数据
- 调用 LLM 解析数据并生成固定模板格式的文本分析报告
- 支持批量分析多只股票
- 超时重试机制（3 次重试不成功返回失败）

## 2. API 规范

### 2.1 接口信息

- **URL**: `https://stock-analyzer-service-55638944338.us-central1.run.app/stock/analyze`
- **Method**: POST
- **Content-Type**: application/json

### 2.2 请求格式

```json
{
  "symbols": ["NVDA", "AAPL"]
}
```

### 2.3 响应格式

```json
{
  "status_code": 200,
  "data": [
    {
      "symbol": "NVDA",
      "stock_name": "NVIDIA Corporation Common Stock",
      "price": 177.19,
      "fear_greed": {
        "index": 26.4,
        "label": "😨 恐慌"
      },
      "technical": {
        "factors": [
          {
            "key": "ma",
            "name": "MA均线",
            "status": "震荡/不明确",
            "bullish_signals": [],
            "bearish_signals": ["价格跌破 MA5"]
          }
        ],
        "data_source": "US_yfinance"
      },
      "fundamental": {
        "factors": [
          {
            "key": "trailingPE",
            "name": "市盈率(TTM)",
            "status": "36.09"
          }
        ]
      }
    }
  ]
}
```

## 3. 设计方案

### 3.1 工作流程

1. **接收用户输入**: 股票代码列表（如 "NVDA, AAPL"）
2. **调用外部 API**: 使用 requests 库发送 POST 请求
3. **重试机制**: 超时后最多重试 3 次，每次间隔递增
4. **解析数据**: 提取每只股票的技术面、基本面、贪恐指数数据
5. **生成报告**: 使用 LLM 将数据填充到固定模板
6. **输出结果**: 返回格式化的文本分析报告

### 3.2 固定报告模板

```markdown
# {股票名称} ({股票代码}) 分析报告
## 基本信息
- 当前价格: ${price}
- 贪恐指数: {index} ({label})

## 技术面分析
### 关键指标
- MA均线: {status}
- MACD: {status}
- RSI: {status}
- KDJ: {status}
- 布林带: {status}

### 信号汇总
看涨信号: {signals}
看跌信号: {signals}

## 基本面分析
### 估值指标
- 市盈率(TTM): {value}
- 市净率: {value}
- EV/EBITDA: {value}
- 市值: {value}

### 财务指标
- 毛利率: {value}
- 营业利润率: {value}
- ROE: {value}
- 营收增长: {value}

## 综合建议
[由 LLM 生成综合分析]
```

### 3.3 重试机制

- 使用 `tenacity` 库实现重试
- 最大重试次数: 3
- 等待策略: 指数退避（4s, 8s, 16s）
- 重试条件: ConnectionError, TimeoutError, HTTPError

## 4. Skill 结构

```
stock-analyzer/
├── SKILL.md                    # Skill 定义文件
├── references/
│   └── api_template.md         # API 请求模板和重试逻辑
│   └── report_template.md      # 分析报告固定模板
```

## 5. 关键实现细节

### 5.1 API 调用

```python
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=16)
)
def fetch_stock_data(symbols: List[str]) -> dict:
    response = requests.post(
        "https://stock-analyzer-service-55638944338.us-central1.run.app/stock/analyze",
        json={"symbols": symbols},
        timeout=30
    )
    return response.json()
```

### 5.2 报告生成

- 使用 LLM 将原始数据填充到固定模板
- 每只股票生成独立报告
- 批量股票时使用分隔符区分

## 6. 验收标准

1. ✅ 能成功调用外部 API 并获取数据
2. ✅ 超时重试 3 次后才返回失败
3. ✅ 支持批量分析多只股票
4. ✅ 输出固定模板格式的分析报告
5. ✅ 报告包含技术面、基本面、贪恐指数数据
6. ✅ 错误处理清晰（重试失败、无效股票代码等）
