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
}

export interface StockAnalysisRequest {
  symbols: string[]
}
