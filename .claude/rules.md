# 开发规则

## 核心原则
- 先读后改，小步迭代，保持架构
- 不猜测，所有结论写入 `.claude/context.md`
- 输出后检查中文字符是否乱码

## 代码规范

### Python
| 约定 | 说明 |
|------|------|
| 命名 | snake_case (文件/函数), PascalCase (类) |
| 类型 | 必须标注参数和返回值 |
| 异步 | I/O 操作使用 async/await |
| 注释 | 中文文档字符串 |

### TypeScript
| 约定 | 说明 |
|------|------|
| 命名 | PascalCase (组件), camelCase (变量) |
| 类型 | 优先 interface，联合用 type |
| 组件 | 函数组件 + Hooks |

### 文件命名
- Python: `snake_case.py`
- React: `PascalCase.tsx`
- 类型: `*.ts`

## 架构约束

### 数据源规范
第三方数据源 API 调用必须集中在 `data_provider/sources/xxx.py`:
- Tushare → `sources/tushare.py`
- AkShare → `sources/akshare.py`
- yfinance → `sources/nasdaq.py`

`loader.py` 只负责策略选择和格式标准化，不直接调用第三方 API。

### Agent 开发
```python
class CustomAgent(BaseAgent):
    async def analyze(self, state: AnalysisState, progress_callback=None) -> AnalysisState:
        # 错误处理：不抛异常，记录到 state
        try:
            # 分析逻辑
        except Exception as e:
            state.set_error("AgentName", str(e))
        return state
```

### 因子开发
```python
FactorDetail(
    name="因子名称",
    value=0.5,          # 0-1 归一化
    signal="bullish",   # bullish/bearish/neutral
)
```

### API 响应
```python
{"status_code": 200, "data": {...}, "err_msg": null}
```

### SSE 事件
- 事件名: `start`, `progress`, `thinking`, `streaming`, `complete`, `error`
- progress 格式: `step:status` (如 `fundamental:running`)

## 禁区

| 禁止 | 正确做法 |
|------|----------|
| 同步 I/O | async/await |
| Agent 抛异常 | `state.set_error()` |
| 硬编码配置 | `os.getenv()` |
| Agent 操作 DB | 通过 DataLoader/CacheUtil |
| 前端 `any` 类型 | 定义 interface |
| Bash 读文件 | 用 Read 工具 |
| Bash 改文件 | 用 Edit 工具 |

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DEEPSEEK_API_KEY` | AI 分析 (推荐) | - |
| `OPENAI_API_KEY` | AI 分析 (备选) | - |
| `TUSHARE_TOKEN` | A 股数据 | - |
| `ENV` | development/production | development |
| `PORT` | 服务端口 | 8080 |
| `CACHE_DIR` | 缓存目录 | .cache/ |

## 重要代码位置

| 功能 | 路径 |
|------|------|
| 配置 | `src/config.py` |
| 流程编排 | `src/core/pipeline.py` |
| Agent 基类 | `src/agents/base.py` |
| 协调 Agent | `src/agents/coordinator/agent.py` |
| 因子基类 | `src/analyzer/base.py` |
| 数据加载 | `src/data_provider/loader.py` |
| 缓存 | `src/storage/cache.py` |
| 前端 API | `web/src/api/client.ts` |

## 技术债务

1. Qlib 158 因子库未完全集成
2. 美股基本面数据不如 A 股完整
3. 前端 SSE 断线无自动重连

## Git 提交

```
<type>: <subject>
feat/fix/perf/refactor/docs/chore
```

---
*更新: 2026-02-22*
