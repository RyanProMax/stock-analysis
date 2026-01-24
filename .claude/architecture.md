# 架构与运行链路

## 整体架构

```
前端 (React) → API 层 → Agent 层 → 服务层 → 指标层 → 数据层 → 核心层
```

### Agent 层
- `FundamentalAgent` - 基本面分析
- `TechnicalAgent` - 技术面分析
- `CoordinatorAgent` - LLM 综合分析 + 流式输出

### SSE 事件类型
| 事件 | 说明 |
|------|------|
| `start` | 分析开始 |
| `progress` | 进度更新 (包含 factors) |
| `thinking` | LLM 思考过程 |
| `streaming` | LLM 正常输出 |
| `complete` | 完成结果 |

## 前端核心: agent-report/

### AgentStep 枚举
```tsx
enum AgentStep {
  Fundamental = 'fundamental_analyzer',
  Technical = 'technical_analyzer',
  Coordinator = 'coordinator',
}
```

### 组件职责
| 文件 | 职责 |
|------|------|
| `index.tsx` | 主容器，AgentStep 枚举，SSE 事件处理，内容过滤 |
| `StepCard.tsx` | 步骤卡片，点击切换 selectedStep |
| `ThinkingAndReport.tsx` | 思考过程 + 报告展示 |

### 内容过滤逻辑
| selectedStep | 因子列表 | 报告组件 |
|--------------|----------|----------|
| `Fundamental` | 仅基本面 | 仅基本面报告 |
| `Technical` | 仅技术面 | 仅技术面报告 |
| `Coordinator` | 全部显示 | 仅综合报告 |

## 后端核心路径

```
/agent/analyze → SSE 流式响应
  → FundamentalAgent.analyze() + TechnicalAgent.analyze() (并行)
  → CoordinatorAgent.synthesize_stream() (综合分析)
```

## 数据获取优先级
A 股: Tushare → AkShare → 新浪
美股: yfinance
