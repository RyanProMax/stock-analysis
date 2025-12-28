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
  type: 'start' | 'progress' | 'error' | 'complete'
  timestamp?: string
}

// 开始事件
export interface StartEvent extends BaseSSEEvent {
  type: 'start'
  message: string
  symbol: string
}

// 进度事件
export interface ProgressEvent extends BaseSSEEvent {
  type: 'progress'
  step: string
  status: string
  message: string
  data?: any
  timestamp: string
}

// 错误事件
export interface ErrorEvent extends BaseSSEEvent {
  type: 'error'
  message: string
  step?: string
}

// 完���事件 - 分析结果
export interface AnalysisFactor {
  status: string
  signals?: string[]
  score?: number
  details?: Record<string, any>
}

export interface AnalysisResult {
  symbol: string
  recommendation: string
  score: number
  summary: string
  technical_analysis?: Record<string, AnalysisFactor>
  fundamental_analysis?: Record<string, AnalysisFactor>
  qlib_analysis?: Record<string, AnalysisFactor>
  key_factors?: {
    positive: string[]
    negative: string[]
  }
  price_target?: {
    target: number
    current: number
    upside_potential: number
  }
  timestamp?: string
}

export interface CompleteEvent extends BaseSSEEvent {
  type: 'complete'
  message: string
  result: AnalysisResult
}

// Agent报告联合类型
export type AgentReportEvent = StartEvent | ProgressEvent | ErrorEvent | CompleteEvent

// 向后兼容的消息类型（用于内部状态管理）
export interface ProgressNode {
  step: string
  status: 'running' | 'completed' | 'error'
  message: string
  data?: any
}
