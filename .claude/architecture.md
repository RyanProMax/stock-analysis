# stock-analysis 项目架构

## 基本信息
- **路径**: `/home/ryan/projects/stock-analysis`
- **类型**: FastAPI 后端 + React 前端，服务型
- **技术栈**: FastAPI/Python 3.12+, LangGraph, OpenAI/DeepSeek, React 18, Ant Design, TailwindCSS
- **数据源**: tushare, akshare, yfinance
- **入口**: `server/main.py` (FastAPI), `web/src/index.tsx` (React)

## 目录结构
```
server/src/
├── config.py         # 全局配置 + 环境判断
├── api/routes/       # stock, agent, index 路由
├── core/             # models, constants, pipeline
├── agents/           # Multi-Agent (LangGraph)
│   ├── coordinator/  # 协调器 Agent
│   ├── fundamental/  # 基本面 Agent
│   └── technical/    # 技术面 Agent
├── analyzer/         # 因子计算 (技术/基本面/qlib158)
├── data_provider/    # loader, stock_list, sources/
├── storage/          # cache, models (ORM预留)
└── notification/     # formatters
```

## 架构层级与核心模块

```
前端 (React) → API 层 → Core/Pipeline → Agent 层 → Analyzer 层 → Data Provider 层
                                    ↓
                              Storage 层 (缓存)
```

| 层 | 目录 | 核心模块 | 职责 |
|---|------|----------|------|
| API | `api/routes/` | - | HTTP 协议处理、参数校验、响应封装 |
| Core | `core/` | `pipeline` | 流程编排、数据模型 |
| Agents | `agents/` | `coordinator`, `llm` | Multi-Agent 分析系统 |
| Analyzer | `analyzer/` | `multi_factor` | 因子计算 (技术/基本面/qlib158) |
| Data Provider | `data_provider/` | `loader` | 多数据源获取、统一接口 |
| Storage | `storage/` | `cache` | 缓存 + 持久化 (预留) |
| Notification | `notification/` | `formatters` | 消息格式化 |

## Agent 系统

### Agent 职责
- `FundamentalAgent` - 基本面分析
- `TechnicalAgent` - 技术面分析
- `CoordinatorAgent` - LLM 综合分析 + 流式输出

### 并行执行
FundamentalAgent 和 TechnicalAgent 并行执行，使用 `asyncio.create_task` + Queue 收集进度。

### LLM 思维链
LLM 返回的思考过程通过接口专用字段 `reasoning` 返回，与正常内容 `content` 分离，前端通过不同事件类型 (`thinking`/`streaming`) 展示。

## 请求流程

### 批量分析
```
POST /stock/analyze → pipeline.batch_analyze() → DataLoader → 因子计算 → JSON
```

### 流式分析 (SSE)
```
GET /agent/analyze
  → FundamentalAgent.analyze() + TechnicalAgent.analyze() (并行)
  → CoordinatorAgent.synthesize_stream() (综合分析)
  → SSE 事件流
```

### SSE 事件类型
| 事件 | 说明 |
|------|------|
| `start` | 分析开始 |
| `progress` | 进度更新 (包含 factors) |
| `thinking` | LLM 思考过程 (reasoning 字段) |
| `streaming` | LLM 正常输出 (content 字段) |
| `complete` | 完成结果 |

## 数据源策略

### 优先级
- **A 股**: Tushare → AkShare → 新浪
- **美股**: yfinance

### 缓存
- 北京时间 6:00 AM 刷新缓存
- 本地 `.cache/` 目录或 GCS

## 前端架构

### agent-report 组件
| 文件 | 职责 |
|------|------|
| `index.tsx` | 主容器，SSE 事件处理 |
| `StepCard.tsx` | 步骤卡片 |
| `ThinkingAndReport.tsx` | 思考过程 + 报告 |

### AgentStep 枚举
```tsx
enum AgentStep {
  Fundamental = 'fundamental_analyzer',
  Technical = 'technical_analyzer',
  Coordinator = 'coordinator',
}
```

## import 快速参考

```python
from src.config import is_development, is_production, config
from src.data_provider import DataLoader, StockListService
from src.storage import CacheUtil
from src.analyzer import MultiFactorAnalyzer
from src.core.pipeline import stock_service
from src.notification.formatters import console_report
```

## 数据结构

### FactorDetail
```python
{
    "name": "因子名称",
    "value": 0.5,          # 0-1 归一化
    "signal": "bullish",   # bullish/bearish/neutral
}
```

### AnalysisState
```python
{
    "symbol": "NVDA",
    "stock_name": "NVIDIA Corporation",
    "fundamental_analysis": "基本面分析...",
    "technical_analysis": "技术面分析...",
    "fundamental": {"factors": [...], "data_source": "..."},
    "technical": {"factors": [...], "data_source": "..."},
    "errors": {},
}
```

## 开发环境

### Token 限制
- 开发环境 LLM `max_tokens=500`
- 位置: `get_max_tokens()` in `agents/coordinator/agent.py`

### 启动命令
```bash
# 后端
cd server && poetry run python main.py

# 前端
cd web && pnpm run dev
```

---
*更新: 2026-02-22*
