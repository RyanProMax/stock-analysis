export interface ComponentProps {
  isMobile: boolean
}

export const TabKey = {
  StockAnalysis: 'stock-analysis',
} as const

export type TabKey = (typeof TabKey)[keyof typeof TabKey]

export const Tabs = [{ id: TabKey.StockAnalysis, label: '分析' }]
