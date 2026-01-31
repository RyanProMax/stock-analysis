# 约定 & 禁区

## 代码规范

### Python (后端)

| 约定 | 说明 |
|------|------|
| 命名风格 | snake_case (文件/函数/变量), PascalCase (类) |
| 类型注解 | 必须使用，参数和返回值都要标注 |
| 字符串 | 中文注释和文档字符串，代码变量用英文 |
| 异步 | 所有 I/O 操作使用 async/await |
| 错误处理 | 单个 Agent 失败不影响整体，记录到 state.errors |

### TypeScript (前端)

| 约定 | 说明 |
|------|------|
| 命名风格 | PascalCase (组件/类型), camelCase (变量/函数) |
| 类型定义 | 优先使用 interface，联合类型用 type |
| 组件结构 | 函数组件 + Hooks |
| 状态管理 | 组件内部用 useState，跨组件用 props/context |

### 文件命名

| 类型 | 约定 | 示例 |
|------|------|------|
| Python 文件 | snake_case.py | `technical_factors.py` |
| React 组件 | PascalCase.tsx | `AgentReport.tsx` |
| 类型文件 | *.ts | `api/client.ts` |
| 工具文件 | *.utils.ts | `date.utils.ts` |

## 架构约定

### Agent 开发

1. **继承 BaseAgent**
   ```python
   class CustomAgent(BaseAgent):
       async def analyze(self, state: AnalysisState, progress_callback=None) -> AnalysisState:
           # 实现分析逻辑
           return state
   ```

2. **进度回调格式**
   ```python
   await progress_callback(step, status, message, data)
   # step: Agent 名称 (如 "fundamental")
   # status: "running" | "completed" | "error"
   # message: 中文描述
   # data: 可选附加数据 (如 factors 列表)
   ```

3. **错误处理**
   ```python
   try:
       # 分析逻辑
   except Exception as e:
       state.set_error("AgentName", str(e))
       return state  # 不要抛出异常
   ```

### 因子开发

1. **继承 BaseFactor**
   ```python
   class CustomFactor(BaseFactor):
       def calculate(self, **kwargs) -> FactorDetail:
           # 计算逻辑
           return FactorDetail(...)
   ```

2. **返回值规范**
   ```python
   FactorDetail(
       name="因子名称",
       value=0.5,          # 0-1 归一化值
       raw_value=100,      # 原始值
       signal="bullish",   # bullish/bearish/neutral
       description="中文描述"
   )
   ```

3. **归一化**
   - 使用 `_clamp_ratio(value)` 确保 0-1 范围
   - 值越大越看多，越小越看空

### API 开发

1. **响应格式统一**
   ```python
   {
       "status_code": 200,
       "data": {...},
       "err_msg": null
   }
   ```

2. **SSE 事件命名**
   - 使用小写: `start`, `progress`, `thinking`, `streaming`, `complete`, `error`
   - progress 事件使用 `step:status` 格式: `fundamental:running`

3. **股票代码处理**
   ```python
   symbol = symbol.upper()  # 统一大写
   ```

## 前端约定

### 组件结构

```typescript
// 组件文件结构
import { useState, useEffect } from 'react'
import type { ComponentProps } from './types'

export function ComponentName({ prop1, prop2 }: ComponentProps) {
  // 1. 状态定义
  const [state, setState] = useState(...)

  // 2. 副作用
  useEffect(() => {...}, [])

  // 3. 事件处理
  const handleClick = () => {...}

  // 4. 渲染
  return <div>...</div>
}
```

### API 调用

```typescript
// 使用 stockApi
import { stockApi } from '@/api/client'

const data = await stockApi.analyzeStocks(['NVDA'])

// SSE 调用
const es = stockApi.getAgentReport(
  'NVDA',
  (event) => { /* onMessage */ },
  { onError: ..., onComplete: ... }
)
```

### 样式约定

- 优先使用 TailwindCSS 工具类
- 复杂组件用 Ant Design
- 移动端用 Ant Design Mobile

## 禁区

### ❌ 不要做的事

1. **同步 I/O 操作**
   ```python
   # ❌ 错误
   def get_data():
       return requests.get(url)  # 同步阻塞

   # ✅ 正确
   async def get_data():
       return await aiohttp.get(url)
   ```

2. **直接抛出异常中断流程**
   ```python
   # ❌ 错误
   raise ValueError("数据获取失败")

   # ✅ 正确
   state.set_error("AgentName", "数据获取失败")
   return state
   ```

3. **硬编码环境相关配置**
   ```python
   # ❌ 错误
   API_URL = "http://localhost:8080"

   # ✅ 正确
   API_URL = os.getenv("API_URL", "http://localhost:8080")
   ```

4. **在 Agent 中直接操作数据库/文件**
   - Agent 只做分析，数据获取通过 DataLoader
   - 缓存操作通过 CacheUtil

5. **前端直接使用 any 类型**
   ```typescript
   // ❌ 错误
   function foo(data: any) {...}

   // ✅ 正确
   interface DataType { ... }
   function foo(data: DataType) {...}
   ```

6. **忽略错误处理**
   - 所有 API 调用必须 try-catch
   - SSE 连接必须处理 onerror

7. **修改核心 Base 类的签名**
   - BaseFactor.calculate() 签名不可变
   - BaseAgent.analyze() 签名不可变

## 环境变量

### LLM 配置

| 变量 | 必需 | 说明 | 默认值 |
|------|:----:|------|--------|
| `DEEPSEEK_API_KEY` | 否 | AI 分析功能（DeepSeek Reasoner，推荐） | - |
| `OPENAI_API_KEY` | 否 | AI 分析功能（OpenAI 备选） | - |

### 数据源配置

| 变量 | 必需 | 说明 | 默认值 |
|------|:----:|------|--------|
| `TUSHARE_TOKEN` | 否 | A 股数据主数据源（优先级最高） | - |

### 服务配置

| 变量 | 必需 | 说明 | 默认值 |
|------|:----:|------|--------|
| `ENV` | 否 | 环境标识：`development`/`dev`/`production`/`prod` | `development` |
| `PORT` | 否 | 服务端口 | `8080` |
| `DEBUG` | 否 | 调试模式（设为 `true` 启用开发模式） | `false` |

### 缓存配置

| 变量 | 必需 | 说明 | 默认值 |
|------|:----:|------|--------|
| `GCS_CACHE_BUCKET` | 否 | 生产环境 Google Cloud Storage Bucket 名称 | - |
| `CACHE_DIR` | 否 | 本地缓存目录路径 | `.cache/` |

> **注意**：没有 API Key 时系统仍可运行，使用备用数据源（AkShare/新浪）和简化分析（无 AI 综合建议）。

## Git 提交

```
# 提交格式
<type>: <subject>

# type 类型
feat:     新功能
fix:      Bug 修复
perf:     性能优化
refactor: 重构
docs:     文档
chore:    构建/工具

# 示例
feat: 添加美股数据支持
fix: 修复因子计算错误
perf: 优化数据加载速度
```
