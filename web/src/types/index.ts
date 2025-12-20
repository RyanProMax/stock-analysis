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

// Agent报告消息类型
export interface AgentReportMessage {
  node: string
  status: 'running' | 'completed' | 'error'
  progress?: number
  message?: string
  data?: any
  content?: string
  error?: string
}
