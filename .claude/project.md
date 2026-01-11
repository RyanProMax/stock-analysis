# 项目概述

## 项目名称

**Stock Analysis System** - 股票分析系统

## 项目定位

一个支持 **A 股** 和 **美股** 的智能股票分析平台，结合传统量化指标与 AI 驱动的综合分析，提供投资决策支持。

## 核心功能

### 1. 多因子分析
- **技术面分析**：MA、EMA、MACD、RSI、KDJ、布林带、ATR 等 15+ 技术指标
- **基本面分析**：PE、PB、ROE、营收增长、负债率等核心财务指标
- **量化因子**：可选的 158 个 Qlib 量化因子

### 2. AI 智能分析
- **多 Agent 架构**：基本面 Agent、技术面 Agent、协调 Agent 并行工作
- **流式输出**：SSE 实时推送分析进度和结果
- **思维链展示**：支持 `<thinking>` 标签展示推理过程

### 3. 数据源支持
- **A 股**：Tushare（主）→ AkShare（备）→ 新浪（兜底）
- **美股**：yfinance
- **缓存策略**：内存 + GCS/本地持久化，北京时间 6:00 自动刷新

## 技术栈

### 后端
- **框架**：FastAPI (Python 3.12+)
- **并发**：asyncio 全异步
- **AI**：LangGraph 思路 + OpenAI API
- **数据**：pandas、stockstats
- **部署**：Docker

### 前端
- **框架**：React 19 + TypeScript
- **构建**：Vite
- **UI**：Ant Design（桌面）+ Ant Design Mobile（移动）
- **样式**：TailwindCSS
- **API**：Axios + SSE

## API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/agent/analyze` | GET | 流式分析（SSE），主要接口 |
| `/stock/analyze` | POST | 批量分析（JSON），传统接口 |
| `/stock/list` | GET | 获取股票列表 |
| `/ping` | GET | 健康检查 |

## 项目结构

```
stock-analysis/
├── server/                    # Python 后端
│   ├── src/
│   │   ├── agent/            # Agent 架构
│   │   │   ├── base.py       # 基类和状态管理
│   │   │   ├── coordinator/  # 协调 Agent
│   │   │   ├── fundamental/  # 基本面 Agent
│   │   │   ├── technical/    # 技术面 Agent
│   │   │   └── llm.py        # LLM 管理器
│   │   ├── controller/       # API 层
│   │   ├── service/          # 业务逻辑层
│   │   │   ├── factors/      # 因子库
│   │   │   └── data_loader/  # 数据加载
│   │   └── env.py            # 环境配置
│   └── main.py               # 应用入口
└── web/                       # React 前端
    └── src/
        ├── api/              # API 客户端
        ├── components/       # 组件
        └── types/            # 类型定义
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `PORT` | 服务端口 | 8080 |
| `ENV` | 环境 (dev/prod) | - |
| `DEBUG` | 调试模式 | false |
| `TUSHARE_TOKEN` | Tushare API Token | - |
| `GCS_CACHE_BUCKET` | GCS 缓存桶 | - |
| `CACHE_DIR` | 本地缓存目录 | - |
| `OPENAI_API_KEY` | OpenAI API Key | - |
| `OPENAI_BASE_URL` | OpenAI API Base | - |

## 开发命令

```bash
# 安装依赖
pnpm install

# 启动前后端
pnpm run dev

# 仅后端
cd server && poetry run python main.py

# 仅前端
cd web && pnpm run dev
```
