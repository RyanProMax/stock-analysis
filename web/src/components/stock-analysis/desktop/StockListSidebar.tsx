import React from 'react'
import { X, ChevronRight } from 'lucide-react'
import type { AnalysisReport } from '../../../types'

interface StockListSidebarProps {
  symbolList: string[]
  reports: Map<string, AnalysisReport>
  selectedSymbol: string | null
  onSelectSymbol: (symbol: string) => void
  onRemoveSymbol: (symbol: string) => void
}

// 获取贪恐指数主题
const getFearGreedTheme = (index: number) => {
  if (index >= 80) return { bg: 'bg-emerald-500', ring: '#10b981' }
  if (index >= 60) return { bg: 'bg-emerald-400', ring: '#34d399' }
  if (index >= 40) return { bg: 'bg-amber-400', ring: '#f59e0b' }
  if (index >= 20) return { bg: 'bg-rose-400', ring: '#f43f5e' }
  return { bg: 'bg-rose-500', ring: '#dc2626' }
}

// 判断是否是美股
const isUSStock = (symbol: string) => {
  return /^[A-Z]+$/.test(symbol) && !/^\d+$/.test(symbol)
}

// 获取显示名称
const getDisplayName = (symbol: string, report?: AnalysisReport) => {
  if (!report) return symbol
  return isUSStock(symbol) ? report.symbol : report.stock_name || report.symbol
}

export const StockListSidebar: React.FC<StockListSidebarProps> = ({
  symbolList,
  reports,
  selectedSymbol,
  onSelectSymbol,
  onRemoveSymbol,
}) => {
  return (
    <div className="w-80 shrink-0">
      <div className="space-y-2 overflow-y-auto pr-2" style={{ maxHeight: 'calc(100vh - 300px)' }}>
        {symbolList.length === 0 ? (
          <div className="flex items-center justify-center rounded-xl border border-dashed border-gray-300 bg-gray-50 px-4 py-8 text-center dark:border-gray-700 dark:bg-gray-800/60">
            <p className="text-sm text-gray-500 dark:text-gray-400">暂无股票，请添加股票代码</p>
          </div>
        ) : (
          symbolList.map(symbol => {
            const report = reports.get(symbol)
            const displayName = getDisplayName(symbol, report)
            const isSelected = selectedSymbol === symbol
            const theme = report ? getFearGreedTheme(report.fear_greed.index) : null

            return (
              <div
                key={symbol}
                className={`group relative cursor-pointer rounded-lg border transition-all ${
                  isSelected
                    ? 'border-gray-400 bg-gray-100 dark:border-gray-600 dark:bg-gray-800'
                    : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:hover:border-gray-600 dark:hover:bg-gray-800/80'
                }`}
                onClick={() => onSelectSymbol(symbol)}
              >
                <div className="flex items-center gap-3 p-3">
                  {/* 展开/选中指示器 */}
                  <div
                    className={`shrink-0 transition-transform ${
                      isSelected
                        ? 'rotate-90 text-gray-600 dark:text-gray-400'
                        : 'text-gray-300 dark:text-gray-600'
                    }`}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </div>

                  {/* 股票信息 */}
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="truncate text-sm font-medium text-gray-900 dark:text-gray-100">
                        {displayName}
                      </h3>
                      {report && (
                        <span className="shrink-0 text-xs font-semibold text-gray-900 dark:text-gray-100">
                          ${report.price.toFixed(2)}
                        </span>
                      )}
                    </div>

                    {/* 贪恐指数进度条 */}
                    {report && theme && (
                      <div className="mt-1.5 flex items-center gap-2">
                        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
                          <div
                            className="h-full rounded-full transition-all duration-1000 ease-out"
                            style={{
                              width: `${report.fear_greed.index}%`,
                              backgroundColor: theme.ring,
                            }}
                          />
                        </div>
                        <span className="shrink-0 text-xs text-gray-500 dark:text-gray-400">
                          {report.fear_greed.index.toFixed(0)}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* 删除按钮 */}
                  <button
                    onClick={e => {
                      e.stopPropagation()
                      onRemoveSymbol(symbol)
                    }}
                    className="shrink-0 rounded p-1 text-gray-400 opacity-0 transition-opacity hover:bg-gray-200 hover:text-gray-600 group-hover:opacity-100 dark:hover:bg-gray-700 dark:hover:text-gray-300"
                    aria-label="删除"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
