import { ChevronDown, ChevronUp, TrendingUp, TrendingDown } from 'lucide-react'
import { useState } from 'react'
import type { AnalysisReport, FactorDetail } from '../../types'

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
            <h2 className="w-20 truncate text-2xl font-light text-gray-900 dark:text-gray-100">
              {report.symbol}
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
          {/* 基本面因子 */}
          {fundamentalFactors.length > 0 && (
            <div className="mb-6 last:mb-0">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-base font-light text-gray-900 dark:text-gray-100">基本面</h3>
                <button
                  onClick={e => {
                    e.stopPropagation()
                    const categoryFactorKeys = fundamentalFactors.map(
                      f => `${report.symbol}-${f.key}`
                    )
                    const allExpanded = categoryFactorKeys.every(key => expandedFactors.has(key))
                    toggleAllFactors(fundamentalFactors, !allExpanded)
                  }}
                  className="rounded-lg px-3 py-1.5 text-xs font-light text-gray-600 dark:text-gray-400 transition-colors hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  {fundamentalFactors.every(f => expandedFactors.has(`${report.symbol}-${f.key}`))
                    ? '收起全部'
                    : '展开全部'}
                </button>
              </div>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
                {fundamentalFactors.map(factor => {
                  const factorKey = `${report.symbol}-${factor.key}`
                  const isExpanded = expandedFactors.has(factorKey)
                  const factorStatus = getFactorStatus(factor)
                  const statusStyle = getFactorStatusStyle(factorStatus)

                  return (
                    <FactorItem
                      key={factor.key}
                      factor={factor}
                      isExpanded={isExpanded}
                      statusStyle={statusStyle}
                      onToggle={() => toggleFactor(factorKey)}
                    />
                  )
                })}
              </div>
            </div>
          )}

          {/* 技术面因子 */}
          {technicalFactors.length > 0 && (
            <div className="mb-6 last:mb-0">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-base font-light text-gray-900 dark:text-gray-100">技术面</h3>
                <button
                  onClick={e => {
                    e.stopPropagation()
                    const categoryFactorKeys = technicalFactors.map(
                      f => `${report.symbol}-${f.key}`
                    )
                    const allExpanded = categoryFactorKeys.every(key => expandedFactors.has(key))
                    toggleAllFactors(technicalFactors, !allExpanded)
                  }}
                  className="rounded-lg px-3 py-1.5 text-xs font-light text-gray-600 dark:text-gray-400 transition-colors hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  {technicalFactors.every(f => expandedFactors.has(`${report.symbol}-${f.key}`))
                    ? '收起全部'
                    : '展开全部'}
                </button>
              </div>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
                {technicalFactors.map(factor => {
                  const factorKey = `${report.symbol}-${factor.key}`
                  const isExpanded = expandedFactors.has(factorKey)
                  const factorStatus = getFactorStatus(factor)
                  const statusStyle = getFactorStatusStyle(factorStatus)

                  return (
                    <FactorItem
                      key={factor.key}
                      factor={factor}
                      isExpanded={isExpanded}
                      statusStyle={statusStyle}
                      onToggle={() => toggleFactor(factorKey)}
                    />
                  )
                })}
              </div>
            </div>
          )}

          {/* Qlib 因子 */}
          {qlibFactors.length > 0 && (
            <div>
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-base font-light text-gray-900 dark:text-gray-100">Qlib因子</h3>
                <button
                  onClick={e => {
                    e.stopPropagation()
                    const categoryFactorKeys = qlibFactors.map(f => `${report.symbol}-${f.key}`)
                    const allExpanded = categoryFactorKeys.every(key => expandedFactors.has(key))
                    toggleAllFactors(qlibFactors, !allExpanded)
                  }}
                  className="rounded-lg px-3 py-1.5 text-xs font-light text-gray-600 dark:text-gray-400 transition-colors hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  {qlibFactors.every(f => expandedFactors.has(`${report.symbol}-${f.key}`))
                    ? '收起全部'
                    : '展开全部'}
                </button>
              </div>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
                {qlibFactors.map(factor => {
                  const factorKey = `${report.symbol}-${factor.key}`
                  const isExpanded = expandedFactors.has(factorKey)
                  const factorStatus = getFactorStatus(factor)
                  const statusStyle = getFactorStatusStyle(factorStatus)

                  return (
                    <FactorItem
                      key={factor.key}
                      factor={factor}
                      isExpanded={isExpanded}
                      statusStyle={statusStyle}
                      onToggle={() => toggleFactor(factorKey)}
                    />
                  )
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

interface FactorItemProps {
  factor: {
    key: string
    name: string
    status: string
    bullish_signals: Array<{ factor: string; message: string }>
    bearish_signals: Array<{ factor: string; message: string }>
  }
  isExpanded: boolean
  statusStyle: {
    bg: string
    text: string
    border: string
    dot: string
    detailBg: string
    detailText: string
  }
  onToggle: () => void
}

const FactorItem: React.FC<FactorItemProps> = ({ factor, isExpanded, statusStyle, onToggle }) => {
  return (
    <div
      className={`overflow-hidden rounded-lg border transition-all ${
        isExpanded
          ? `${statusStyle.border} ${statusStyle.bg}`
          : 'border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800'
      }`}
    >
      {/* 因子头部 */}
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 text-left transition-colors hover:bg-gray-50 dark:hover:bg-gray-700/50"
      >
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className={`h-2 w-2 rounded-full ${statusStyle.dot}`} />
              <h4 className="text-sm font-light text-gray-900 dark:text-gray-100">{factor.name}</h4>
            </div>
            <p className="mt-1 text-xs text-gray-600 dark:text-gray-400">{factor.status || '-'}</p>
          </div>
          {isExpanded ? (
            <ChevronUp className="h-4 w-4 text-gray-400" />
          ) : (
            <ChevronDown className="h-4 w-4 text-gray-400" />
          )}
        </div>
      </button>

      {/* 因子详情（展开时显示） */}
      {isExpanded && (
        <div className={`border-t px-4 py-3 ${statusStyle.border} ${statusStyle.detailBg}`}>
          {/* 看涨信号 */}
          {factor.bullish_signals.length > 0 && (
            <div className="mb-3">
              <div className="mb-2 flex items-center gap-2">
                <TrendingUp className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                <h5 className={`text-xs font-light ${statusStyle.detailText}`}>看涨信号</h5>
              </div>
              <ul className="space-y-1.5">
                {factor.bullish_signals.map((signal, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />
                    <span className={`text-xs leading-relaxed ${statusStyle.detailText}`}>
                      {signal.message}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 看跌信号 */}
          {factor.bearish_signals.length > 0 && (
            <div>
              <div className="mb-2 flex items-center gap-2">
                <TrendingDown className="h-3.5 w-3.5 text-rose-600 dark:text-rose-400" />
                <h5 className={`text-xs font-light ${statusStyle.detailText}`}>看跌信号</h5>
              </div>
              <ul className="space-y-1.5">
                {factor.bearish_signals.map((signal, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-rose-500" />
                    <span className={`text-xs leading-relaxed ${statusStyle.detailText}`}>
                      {signal.message}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 无信号提示 */}
          {factor.bullish_signals.length === 0 && factor.bearish_signals.length === 0 && (
            <p className={`text-xs italic ${statusStyle.detailText} opacity-70`}>暂无信号</p>
          )}
        </div>
      )}
    </div>
  )
}
