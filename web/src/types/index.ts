// API 响应类型定义
export interface FactorDetail {
  key: string
  name: string
  status: string
  bullish_signals: string[]
  bearish_signals: string[]
}

export interface FearGreed {
  index: number
  label: string
}

export interface AnalysisReport {
  symbol: string
  stock_name: string | null
  price: number
  technical_factors: FactorDetail[]
  fundamental_factors: FactorDetail[]
  qlib_factors: FactorDetail[]
  fear_greed: FearGreed
  status?: 'success' | 'error'
  error?: string
}

export interface StockAnalysisRequest {
  symbols: string[]
}

// 标准API响应格式
export interface StandardResponse<T> {
  status_code: number
  data: T | null
  err_msg: string | null
}

// 股票信息
export interface StockInfo {
  ts_code: string
  symbol: string
  name: string
  area?: string | null
  industry?: string | null
  market?: string | null
  list_date?: string | null
}

// 股票列表响应
export interface StockListResponse {
  stocks: StockInfo[]
  total: number
}

// SSE事件类型基础接口
export interface BaseSSEEvent {
  type: 'start' | 'progress' | 'streaming' | 'thinking' | 'error' | 'complete'
  timestamp?: string
}

// 开始事件
export interface StartEvent extends BaseSSEEvent {
  type: 'start'
  symbol: string
}

// 进度事件
export interface ProgressEvent extends BaseSSEEvent {
  type: 'progress'
  step: string
  status: string
  message: string
  data?: {
    factors?: FactorDetail[]
    execution_time?: number
  }
}

// 流式事件 - LLM 流式输出
export interface StreamingEvent extends BaseSSEEvent {
  type: 'streaming'
  step: string
  content: string
}

// 思考过程事件 - LLM 推理过程
export interface ThinkingEvent extends BaseSSEEvent {
  type: 'thinking'
  step: string
  content: string
}

// 错误事件
export interface ErrorEvent extends BaseSSEEvent {
  type: 'error'
  message: string
}

// 完成事件 - 分析结果
export interface AnalysisFactor {
  status: string
  signals?: string[]
  details?: Record<string, any>
}

export interface AnalysisDecision {
  action: string
  analysis: string
  thinking?: string
}

export interface AnalysisResult {
  symbol: string
  stock_name: string
  decision: AnalysisDecision
  execution_times: Record<string, number>
}

export interface CompleteEvent extends BaseSSEEvent {
  type: 'complete'
  result: AnalysisResult
}

// Agent报告联合类型
export type AgentReportEvent =
  | StartEvent
  | ProgressEvent
  | StreamingEvent
  | ThinkingEvent
  | ErrorEvent
  | CompleteEvent

// 向后兼容的消息类型（用于内部状态管理）
export interface ProgressNode {
  step: string
  status: 'fetching' | 'running' | 'analyzing' | 'completed' | 'error'
  message: string
  data?: any
}
