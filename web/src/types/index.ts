// API 响应类型定义
export interface FactorDetail {
  key: string
  name: string
  status: string
  bullish_signals: string[]
  bearish_signals: string[]
  data_source: string
}

export interface FearGreed {
  index: number
  label: string
}

export interface FactorAnalysis {
  factors: FactorDetail[]
  data_source: string
  raw_data: Record<string, any> | null
}

// 趋势分析枚举类型
export type TrendStatus =
  | '强势多头'
  | '多头排列'
  | '弱势多头'
  | '盘整'
  | '弱势空头'
  | '空头排列'
  | '强势空头'

export type VolumeStatus = '放量上涨' | '放量下跌' | '缩量上涨' | '缩量回调' | '量能正常'

export type BuySignal = '强烈买入' | '买入' | '持有' | '观望' | '卖出' | '强烈卖出'

export type MACDStatus = '零轴上金叉' | '金叉' | '多头' | '上穿零轴' | '下穿零轴' | '空头' | '死叉'

export type RSIStatus = '超买' | '强势买入' | '中性' | '弱势' | '超卖'

// 趋势分析结果
export interface TrendAnalysisResult {
  code: string
  trend_status: TrendStatus
  ma_alignment: string
  trend_strength: number
  ma5: number
  ma10: number
  ma20: number
  ma60: number
  current_price: number
  bias_ma5: number
  bias_ma10: number
  bias_ma20: number
  volume_status: VolumeStatus
  volume_ratio_5d: number
  volume_trend: string
  support_ma5: boolean
  support_ma10: boolean
  resistance_levels: number[]
  support_levels: number[]
  macd_dif: number
  macd_dea: number
  macd_bar: number
  macd_status: MACDStatus
  macd_signal: string
  rsi_6: number
  rsi_12: number
  rsi_24: number
  rsi_status: RSIStatus
  rsi_signal: string
  buy_signal: BuySignal
  signal_score: number
  signal_reasons: string[]
  risk_factors: string[]
}

export interface AnalysisReport {
  symbol: string
  stock_name: string | null
  price: number
  technical: FactorAnalysis
  fundamental: FactorAnalysis
  qlib: FactorAnalysis
  fear_greed: FearGreed
  trend_analysis: TrendAnalysisResult | null
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
  message?: string
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
  timestamp?: string
}

export interface CompleteEvent extends BaseSSEEvent {
  type: 'complete'
  result: AnalysisResult
  message?: string
}

// Agent报告联合类型
export type AgentReportEvent =
  | StartEvent
  | ProgressEvent
  | StreamingEvent
  | ThinkingEvent
  | ErrorEvent
  | CompleteEvent

// 节点状态类型
export enum NodeStatus {
  pending = 'pending',
  fetching = 'fetching',
  running = 'running',
  analyzing = 'analyzing',
  completed = 'completed',
  error = 'error',
}

// 向后兼容的消息类型（用于内部状态管理）
export interface ProgressNode {
  step: string
  status: NodeStatus
  message: string
  data?: any
}
