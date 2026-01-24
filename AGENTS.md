# Agent System Instructions

## 核心原则

- **最小改动** - 只修改必要的代码
- **不破坏架构** - 遵循现有分层和模式
- **先读后写** - 必须先用 Read 理解代码再 Edit

---

## 不可违反的规则

- 不新增依赖、Agent 或图节点（除非明确批准）
- 不合并或拆分现有 Agent
- 不修改数据 schema、状态键、消息格式
- 不改变 Agent 执行顺序和并发逻辑
- 不修改金融计算、信号、决策阈值

---

## Agent 边界

| Agent | 职责 |
|-------|------|
| `FundamentalAgent` | 基本面分析 |
| `TechnicalAgent` | 技术面分析 |
| `CoordinatorAgent` | LLM 综合分析 |

Agent 之间不共享逻辑，数据通过 `AnalysisState` 传递。

---

## 前端约束

### agent-report/ 模块
- `AgentStep` 枚举控制内容过滤
- `StepCard` 点击切换 `selectedStep`
- 不破坏 SSE 事件处理和流式渲染

### Tailwind CSS v4+
- 渐变: `bg-linear-to-r` (不是 `bg-gradient-to-r`)
- 尺寸: `bg-size-[...]` (不是 `bg-[length:...]`)

### StepCard 结构（防止上浮效果）
```tsx
// 外层: 边框容器
<div className={`p-[1.5px] ${isSelected ? 'bg-linear-to-r...' : 'border...'}`}>
  // 内层: 内容容器 (两种状态都有 border，保持高度一致)
  <div className={`border ${isSelected ? 'border-transparent' : 'border-gray-200/60'}`}>
    {/* content */}
  </div>
</div>
```

---

## 后端约束

- 不修改 graph 执行流程
- 保留 streaming/async 行为
- Agent 失败记录到 `state.errors`，不抛异常
- 通过 `progress_callback` 发送进度，格式: `(step, status, message, data)`

---

## 工作流程

1. 理解任务 → 2. 定位代码 (Glob/Grep/Read) → 3. 最小修改 (Edit) → 4. 验证
