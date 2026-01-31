# 股票分析系统

基于多因子模型的股票分析系统，提供技术面和基本面分析，支持 A 股和美股。

🌐 [在线演示](https://ryanpromax.github.io/stock-analysis/)

## 功能特性

- **技术面分析**：MA/EMA/MACD/RSI/KDJ/WR/布林带/ATR/贪恐指数/成交量比率
- **基本面分析**：营收增长率/资产负债率/PE/PB/ROE
- **AI 综合分析**：基于 LangGraph 的流式分析，实时展示推理过程
- **多市场支持**：A 股（Tushare/AkShare）+ 美股（yfinance）

## 技术栈

| 前端 | 后端 |
|------|------|
| React 18, TypeScript | FastAPI, Python 3.12+ |
| Vite, Ant Design | LangGraph, OpenAI |
| TailwindCSS | tushare, akshare, yfinance |

## 快速开始

### 环境要求

- Python 3.12+, Node.js 18+, pnpm

### 安装与启动

```bash
# 安装依赖
pnpm install
cd server && poetry install && cd ..

# 一键启动（前后端同时运行）
pnpm run dev
```

访问：http://localhost:3000 | API 文档：http://localhost:8080/docs

### 配置 API Key（可选）

```bash
cd server && cp .env.example .env
```

编辑 `.env` 文件，添加以下变量获得完整功能：

| 变量 | 说明 | 获取地址 |
|------|------|----------|
| `TUSHARE_TOKEN` | A 股数据 | https://tushare.pro |
| `DEEPSEEK_API_KEY` | AI 分析（推荐） | https://platform.deepseek.com |
| `OPENAI_API_KEY` | AI 分析（备选） | https://platform.openai.com |

> 无 API Key 时系统仍可运行，使用备用数据源和简化分析

## API 接口

| 接口 | 说明 |
|------|------|
| `GET /agent/analyze?symbol=NVDA` | 流式分析（SSE） |
| `POST /stock/analyze` | 批量分析 |
| `GET /stock/list?market=A股` | 股票列表 |

## 部署

```bash
cd server && docker build -t stock-analysis . && docker run -p 8080:8080 stock-analysis
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ENV` | `development` | 环境：development/production |
| `PORT` | `8080` | 服务端口 |
| `DEBUG` | `false` | 调试模式 |
| `GCS_CACHE_BUCKET` | - | 生产环境缓存 Bucket |
| `VITE_API_BASE_URL` | `http://localhost:8080` | 前端 API 地址 |

MIT License
