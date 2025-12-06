// API 响应类型定义
export interface FactorDetail {
  key: string;
  name: string;
  category: string;
  status: string;
  bullish_signals: Array<{
    factor: string;
    message: string;
  }>;
  bearish_signals: Array<{
    factor: string;
    message: string;
  }>;
}

export interface FearGreed {
  index: number;
  label: string;
}

export interface AnalysisReport {
  symbol: string;
  stock_name: string | null;
  price: number;
  factors: FactorDetail[];
  fear_greed: FearGreed;
}

export interface StockAnalysisRequest {
  symbols: string[];
}

