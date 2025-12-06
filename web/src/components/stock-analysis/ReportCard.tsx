import { ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import type { AnalysisReport, FactorDetail } from '../../types'
import { FactorList } from './FactorList'

interface ReportCardProps {
  report: AnalysisReport
}

export const ReportCard: React.FC<ReportCardProps> = ({ report }) => {
  const [expandedFactors, setExpandedFactors] = useState<Set<string>>(new Set())
  const [isStockExpanded, setIsStockExpanded] = useState(false)

  const getFearGreedTheme = (index: number) => {
    if (index >= 80) {
      return {
        bg: 'bg-emerald-50 dark:bg-emerald-900/20',
        text: 'text-emerald-700 dark:text-emerald-300',
        ring: '#10b981',
      }
    }
    if (index >= 60) {
      return {
        bg: 'bg-emerald-50 dark:bg-emerald-900/20',
        text: 'text-emerald-600 dark:text-emerald-400',
        ring: '#34d399',
      }
    }
    if (index >= 40) {
      return {
        bg: 'bg-amber-50 dark:bg-amber-900/20',
        text: 'text-amber-800 dark:text-amber-300',
        ring: '#f59e0b',
      }
    }
    if (index >= 20) {
      return {
        bg: 'bg-rose-50 dark:bg-rose-900/20',
        text: 'text-rose-700 dark:text-rose-300',
        ring: '#f43f5e',
      }
    }
    return {
      bg: 'bg-rose-50 dark:bg-rose-900/20',
      text: 'text-rose-800 dark:text-rose-400',
      ring: '#dc2626',
    }
  }

  const getEmojiFromLabel = (label: string) => {
    const emojiMatch = label.match(
      /[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[\u{1F600}-\u{1F64F}]|[\u{1F680}-\u{1F6FF}]/u
    )
    return emojiMatch ? emojiMatch[0] : ''
  }

  const getFactorStatus = (factor: FactorDetail) => {
    const bullishCount = factor.bullish_signals.length
    const bearishCount = factor.bearish_signals.length
    if (bullishCount > bearishCount) return 'bullish'
    if (bearishCount > bullishCount) return 'bearish'
    return 'neutral'
  }

  const getFactorStatusStyle = (status: 'bullish' | 'bearish' | 'neutral') => {
    switch (status) {
      case 'bullish':
        return {
          bg: 'bg-emerald-50/50 dark:bg-emerald-900/20',
          text: 'text-emerald-700 dark:text-emerald-300',
          border: 'border-emerald-200 dark:border-emerald-800',
          dot: 'bg-emerald-500',
          detailBg: 'bg-emerald-50/30 dark:bg-emerald-900/30',
          detailText: 'text-emerald-900 dark:text-emerald-100',
        }
      case 'bearish':
        return {
          bg: 'bg-rose-50/50 dark:bg-rose-900/20',
          text: 'text-rose-700 dark:text-rose-300',
          border: 'border-rose-200 dark:border-rose-800',
          dot: 'bg-rose-500',
          detailBg: 'bg-rose-50/30 dark:bg-rose-900/30',
          detailText: 'text-rose-900 dark:text-rose-100',
        }
      default:
        return {
          bg: 'bg-amber-50/50 dark:bg-amber-900/20',
          text: 'text-amber-800 dark:text-amber-300',
          border: 'border-amber-200 dark:border-amber-800',
          dot: 'bg-amber-500',
          detailBg: 'bg-amber-50/30 dark:bg-amber-900/30',
          detailText: 'text-amber-900 dark:text-amber-100',
        }
    }
  }

  const toggleFactor = (factorKey: string) => {
    setExpandedFactors(prev => {
      const newSet = new Set(prev)
      if (newSet.has(factorKey)) {
        newSet.delete(factorKey)
      } else {
        newSet.add(factorKey)
      }
      return newSet
    })
  }

  const toggleAllFactors = (factors: FactorDetail[], expand: boolean) => {
    setExpandedFactors(prev => {
      const newSet = new Set(prev)
      factors.forEach(factor => {
        const key = `${report.symbol}-${factor.key}`
        if (expand) {
          newSet.add(key)
        } else {
          newSet.delete(key)
        }
      })
      return newSet
    })
  }

  const technicalFactors = report.technical_factors
  const fundamentalFactors = report.fundamental_factors
  const qlibFactors = report.qlib_factors
  const fearGreedTheme = getFearGreedTheme(report.fear_greed.index)
  const emoji = getEmojiFromLabel(report.fear_greed.label)
  const labelText = report.fear_greed.label
    .replace(
      /[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[\u{1F600}-\u{1F64F}]|[\u{1F680}-\u{1F6FF}]/gu,
      ''
    )
    .trim()

  // 判断是否是美股（美股通常是纯字母代码，A股是数字代码）
  const isUSStock = /^[A-Z]+$/.test(report.symbol) && !/^\d+$/.test(report.symbol)

  // 获取显示名称（美股显示 symbol，A股显示 stock_name）
  const displayName = isUSStock ? report.symbol : report.stock_name || report.symbol

  return (
    <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm transition-shadow hover:shadow-md dark:border-gray-700 dark:bg-gray-800">
      {/* 股票头部信息 - 可点击展开/收起 */}
      <button
        onClick={() => setIsStockExpanded(!isStockExpanded)}
        className="w-full border-b border-gray-200 bg-gray-50 px-4 py-4 text-left transition-colors hover:bg-gray-100 sm:px-6 dark:border-gray-700 dark:bg-gray-900/50 dark:hover:bg-gray-800"
      >
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          {/* 移动端：股票名、当前价格、贪恐指数并排一行 */}
          <div className="flex items-center gap-3 sm:gap-4">
            {isStockExpanded ? (
              <ChevronUp className="h-5 w-5 shrink-0 text-gray-400" />
            ) : (
              <ChevronDown className="h-5 w-5 shrink-0 text-gray-400" />
            )}
            <h2 className="w-[100px] truncate text-xl font-light text-gray-900 dark:text-gray-100">
              {displayName}
            </h2>
            <div className="text-left">
              <p className="hidden text-sm text-gray-500 sm:block dark:text-gray-400">当前价格</p>
              <p className="text-base font-medium text-gray-900 dark:text-gray-100">
                ${report.price.toFixed(2)}
              </p>
            </div>
            {/* 移动端：贪恐指数（进度条+emoji+分数） */}
            <div className="ml-auto flex items-center gap-2 sm:hidden">
              <div className="h-2 w-16 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-700">
                <div
                  className="h-full rounded-full transition-all duration-1000 ease-out"
                  style={{
                    width: `${report.fear_greed.index}%`,
                    backgroundColor: fearGreedTheme.ring,
                  }}
                />
              </div>
              <div className="flex items-center gap-1">
                <span className="text-base">{emoji}</span>
                <span className={`text-sm font-light ${fearGreedTheme.text}`}>
                  {report.fear_greed.index.toFixed(1)}
                </span>
              </div>
            </div>
          </div>

          {/* PC端：显示完整样式（进度条上方显示emoji+分数+标签） */}
          <div className="hidden min-w-[120px] sm:block">
            <div className="mb-1 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-base">{emoji}</span>
                <span className={`text-sm font-light ${fearGreedTheme.text}`}>
                  {report.fear_greed.index.toFixed(1)}
                </span>
              </div>
              <span className={`text-xs font-light ${fearGreedTheme.text}`}>{labelText}</span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-gray-100 dark:bg-gray-700">
              <div
                className="h-full rounded-full transition-all duration-1000 ease-out"
                style={{
                  width: `${report.fear_greed.index}%`,
                  backgroundColor: fearGreedTheme.ring,
                }}
              />
            </div>
          </div>
        </div>
      </button>

      {/* 因子列表 - 可折叠 */}
      {isStockExpanded && (
        <div className="p-4 sm:p-6">
          <FactorList
            title={`基本面 (${fundamentalFactors.length})`}
            factors={fundamentalFactors}
            symbol={report.symbol}
            expandedFactors={expandedFactors}
            onToggleFactor={toggleFactor}
            onToggleAll={toggleAllFactors}
            getFactorStatus={getFactorStatus}
            getFactorStatusStyle={getFactorStatusStyle}
          />

          <FactorList
            title={`技术面 (${technicalFactors.length})`}
            factors={technicalFactors}
            symbol={report.symbol}
            expandedFactors={expandedFactors}
            onToggleFactor={toggleFactor}
            onToggleAll={toggleAllFactors}
            getFactorStatus={getFactorStatus}
            getFactorStatusStyle={getFactorStatusStyle}
          />

          <FactorList
            title={`Qlib因子 (${qlibFactors.length})`}
            factors={qlibFactors}
            symbol={report.symbol}
            expandedFactors={expandedFactors}
            onToggleFactor={toggleFactor}
            onToggleAll={toggleAllFactors}
            getFactorStatus={getFactorStatus}
            getFactorStatusStyle={getFactorStatusStyle}
          />
        </div>
      )}
    </div>
  )
}
