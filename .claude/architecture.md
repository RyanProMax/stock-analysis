# 架构与运行链路

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                         前端 (React)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  StockInput  │  │  AgentReport │  │   Factors    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │ SSE               │ SSE              │            │
└─────────┼───────────────────┼──────────────────┼────────────┘
          │                   │                  │
          ▼                   ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      API 层 (api/)                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  /agent/analyze → SSE 流式响应                       │   │
│  │  /stock/analyze → JSON 批量响应                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Agent 层 (agents/)                        │
│                   数据分析、调度                              │
│  ┌─────────────────┐     ┌─────────────────┐               │
│  │ FundamentalAgent│     │ TechnicalAgent  │               │
│  │  (基本面分析)    │     │  (技术面分析)    │               │
│  └────────┬────────┘     └────────┬────────┘               │
│           │                        │                        │
│           └────────────┬───────────┘                        │
│                        ▼                                    │
│           ┌─────────────────────────┐                       │
│           │  CoordinatorAgent       │                       │
│           │  (LLM 综合分析 + 流式)   │                       │
│           └─────────────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   服务层 (services/)                         │
│                   报告服务编排                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  StockService (统一股票服务)                          │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              技术指标层 (indicators/)                         │
│                   因子计算与分析                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ TechnicalFactor  │  │ FundamentalFactor│                │
│  │     Library      │  │     Library       │                │
│  └──────────────────┘  └──────────────────┘                │
│  ┌──────────────────────────────────────┐                   │
│  │    MultiFactorAnalyzer              │                   │
│  └──────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    数据层 (data/)                            │
│              缓存、拉取数据、格式处理                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  CacheUtil   │  │  DataLoader  │  │ StockListSvc │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  sources (Tushare/AkShare/NASDAQ/yfinance)           │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    核心层 (core/)                            │
│                   数据模型、常量                              │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │   Models     │  │  Constants   │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

## 分析流程

### 流式分析流程 (`/agent/analyze`)

```
1. 客户端发起 SSE 请求
   GET /agent/analyze?symbol=NVDA
   │
   ▼
2. 发送 start 事件
   event: start → {symbol: "NVDA"}
   │
   ▼
3. 并行执行（异步）
   ├─ FundamentalAgent.analyze()
   │   ├─ 获取财务数据
   │   ├─ 计算基本面因子
   │   └─ 发送 progress 事件
   │
   └─ TechnicalAgent.analyze()
       ├─ 获取行情数据
       ├─ 计算技术指标
       └─ 发送 progress 事件
   │
   ▼
4. 等待两个 Agent 完成
   │
   ▼
5. CoordinatorAgent.synthesize_stream()
   ├─ 构建综合 Prompt
   ├─ 调用 LLM 流式生成
   ├─ 解析 <thinking> 标签
   └─ 发送 thinking/streaming 事件
   │
   ▼
6. 发送 complete 事件
   event: complete → {result: {...}}
```

### SSE 事件类型

| 事件 | 数据结构 | 说明 |
|------|----------|------|
| `start` | `{symbol}` | 分析开始 |
| `progress` | `{step, status, message, data}` | 进度更新 |
| `thinking` | `{step, content}` | LLM 思考过程 |
| `streaming` | `{step, content}` | LLM 正常输出 |
| `error` | `{message}` | 错误信息 |
| `complete` | `{result}` | 完成结果 |

## Agent 状态管理

### AnalysisState 结构

```python
@dataclass
class AnalysisState:
    # 基本信息
    symbol: str
    stock_name: str = ""
    industry: str = ""
    price: float = 0.0

    # 数据层
    price_data: Optional[pd.DataFrame] = None
    financial_data: Optional[dict] = None

    # 分析结果（使用 FactorAnalysis 结构）
    fundamental: Optional[FactorAnalysis] = None
    fundamental_analysis: str = ""
    technical: Optional[FactorAnalysis] = None
    technical_analysis: str = ""
    coordinator_analysis: str = ""
    thinking_process: str = ""

    # 状态跟踪
    errors: Dict[str, str] = field(default_factory=dict)
    execution_times: Dict[str, float] = field(default_factory=dict)
```

### Agent 执行模式

```python
# 并行执行
async def analyze_stream(symbol: str):
    # 创建进度队列
    progress_queue = asyncio.Queue()

    # 并行启动
    fund_task = asyncio.create_task(fundamental_agent.analyze(...))
    tech_task = asyncio.create_task(technical_agent.analyze(...))

    # 实时消费进度
    while not both_completed:
        event = await progress_queue.get()
        yield event  # 发送 SSE

    # 综合分析
    stream_gen = coordinator.synthesize_stream(state)
    yield stream_gen  # 返回 LLM 流式生成器
```

## 因子库架构

```
BaseFactor (ABC)
├── calculate() → FactorDetail
└── _clamp_ratio() → float

FactorLibrary (ABC)
└── get_factors() → List[FactorDetail]

    ├── TechnicalFactorLibrary
    │   ├── MAFactor
    │   ├── MACDFactor
    │   ├── RSIFactor
    │   └── ...
    │
    ├── FundamentalFactorLibrary
    │   ├── PEFactor
    │   ├── PBFactor
    │   └── ...
    │
    └── Qlib158FactorLibrary (可选)
        └── 158 个量化因子
```

## 缓存策略

```
┌─────────────────────────────────────────────┐
│              缓存层 (CacheUtil)              │
├─────────────────────────────────────────────┤
│  L1: 内存缓存 (当前会话)                     │
│  L2: 持久化缓存                               │
│      ├─ 生产: GCS (gs://bucket/)             │
│      └─ 开发: 本地文件 (cache/)              │
├─────────────────────────────────────────────┤
│  Key 格式:                                    │
│  - 股票列表: a_stocks_YYYY-MM-DD.json       │
│  - 分析报告: reports/YYYY-MM-DD/SYMBOL.json │
├─────────────────────────────────────────────┤
│  刷新策略: 北京时间 6:00 自动刷新             │
└─────────────────────────────────────────────┘
```

## 前端状态流

```
StockInput 组件
    │
    │ 用户输入股票代码
    ▼
API: getAgentReport(symbol, onMessage)
    │
    │ SSE 事件流
    ▼
AgentReport 组件
    │
    ├─ progress → 更新进度条
    ├─ thinking → 渲染思考过程
    ├─ streaming → 渲染分析结果
    └─ complete → 显示最终报告
```

## 数据获取优先级

### A 股
1. Tushare (需 TOKEN)
2. AkShare (免费)
3. 新浪财经 (兜底)

### 美股
1. yfinance (通过 AkShare)

### 失败处理
- 单个 Agent 失败不影响其他 Agent
- 两个 Agent 都失败才返回错误
- 错误信息记录在 `state.errors`
