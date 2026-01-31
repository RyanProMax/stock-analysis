# 长期认知 (Memory)

> 此文件记录项目开发过程中确认的长期决策和认知，持续追加。

## 项目决策

### 数据源策略
- **A 股优先级**: Tushare → AkShare → 新浪
- **美股数据源**: yfinance
- **原因**: Tushare 最稳定但需 Token，AkShare 免费但有频率限制

### Agent 并行执行
- **决策**: FundamentalAgent 和 TechnicalAgent 并行执行
- **原因**: 数据获取独立，可节省约 50% 时间
- **实现**: 使用 asyncio.create_task + Queue 收集进度

### LLM 思维链展示
- **决策**: 使用 `<thinking>` 标签区分思考过程和结果
- **原因**: 用户想看推理逻辑，增强可信度
- **实现**: CoordinatorAgent 解析 LLM 流式输出，分离 thinking/streaming 事件

### 开发环境 Token 限制
- **决策**: 开发环境 LLM max_tokens=500
- **原因**: 控制成本，开发时无需完整输出
- **位置**: `get_max_tokens()` in coordinator/agent.py

### 缓存刷新时间
- **决策**: 北京时间 6:00 AM 刷新缓存
- **原因**: A 股开盘前数据更新完成
- **实现**: 基于日期的缓存 Key 格式

## 技术债务 / 已知问题

### 待优化项
1. **Qlib 因子库**: 当前 158 因子库可选，未完全集成
2. **美股基本面**: 数据来源依赖 yfinance，指标不如 A 股完整
3. **错误重试**: 数据获取失败后无自动重试机制

### 前端待改进
1. **错误处理**: SSE 断线后无自动重连
2. **加载状态**: 多股票批量分析时状态管理可优化

## 架构演进

### v1 → v2 (当前)
- **变化**: 从单一 Agent 拆分为多 Agent 架构
- **收益**: 并行执行，职责清晰，易于扩展

### 未来考虑
- [ ] LangGraph StateGraph 集成（当前是简化版）
- [ ] Agent 执行历史记录
- [ ] 用户自定义因子权重

## 重要代码位置

| 功能 | 文件路径 |
|------|----------|
| Agent 基类 | `server/src/agents/base.py` |
| 状态定义 | `server/src/agents/base.py:AnalysisState` |
| 协调 Agent | `server/src/agents/coordinator/agent.py` |
| 流式 LLM 解析 | `server/src/agents/coordinator/agent.py:synthesize_stream` |
| 因子基类 | `server/src/indicators/base.py` |
| 技术因子库 | `server/src/indicators/technical_factors.py` |
| 数据加载器 | `server/src/data/loader.py` |
| 缓存工具 | `server/src/data/cache_util.py` |
| SSE 控制器 | `server/src/controller/agent.py` |
| 前端 API | `web/src/api/client.ts` |
| Agent 报告组件 | `web/src/components/agent-report/` |

## 数据格式

### FactorDetail 结构
```python
{
    "name": "因子名称",
    "value": 0.5,          # 0-1 归一化
    "raw_value": 100,      # 原始值
    "signal": "bullish",   # bullish/bearish/neutral
    "description": "中文描述"
}
```

### AnalysisState 关键字段
```python
{
    "symbol": "NVDA",
    "stock_name": "NVIDIA Corporation",
    "industry": "半导体",
    "fundamental_analysis": "基本面分析文本...",
    "technical_analysis": "技术面分析文本...",
    "coordinator_analysis": "综合建议...",
    "thinking_process": "推理过程...",
    "fundamental": {"factors": [...], "data_source": "...", "raw_data": {...}},
    "technical": {"factors": [...], "data_source": "...", "raw_data": {...}},
    "errors": {},
    "execution_times": {}
}
```

## 环境配置记录

### 本地开发
```bash
# 后端
cd server
poetry install
poetry run python main.py

# 前端
cd web
pnpm install
pnpm run dev

# 同时启动
pnpm run dev
```

### Docker 部署
```bash
cd server
task build    # 构建
task run_docker  # 运行
```

## 外部依赖

### API 服务
- **Tushare**: https://tushare.pro (需注册)
- **OpenAI**: https://api.openai.com (或兼容服务)

### Python 包
```toml
[dependencies]
fastapi = "^0.115.0"
pandas = "^2.2.0"
stockstats = "^0.5.0"
sse-starlette = "^2.1.0"
openai = "^1.0.0"
```

### 前端包
```json
{
  "react": "^19.2.0",
  "antd": "^5.0.0",
  "antd-mobile": "^5.0.0",
  "tailwindcss": "^4.1.0",
  "axios": "^1.0.0"
}
```

## 更新日志

| 日期 | 记录 |
|------|------|
| 2026-01-31 | 补全环境变量文档（DEEPSEEK_API_KEY, PORT, DEBUG, CACHE_DIR） |
| 2025-01-11 | 初始创建 .claude 目录结构 |
