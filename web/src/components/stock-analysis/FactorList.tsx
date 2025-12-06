import React from 'react'
import { ChevronDown, ChevronUp, TrendingUp, TrendingDown } from 'lucide-react'
import type { FactorDetail } from '../../types'

interface FactorListProps {
  title: string
  factors: FactorDetail[]
  symbol: string
  expandedFactors: Set<string>
  onToggleFactor: (factorKey: string) => void
  onToggleAll: (factors: FactorDetail[], expand: boolean) => void
  getFactorStatus: (factor: FactorDetail) => 'bullish' | 'bearish' | 'neutral'
  getFactorStatusStyle: (status: 'bullish' | 'bearish' | 'neutral') => {
    bg: string
    text: string
    border: string
    dot: string
    detailBg: string
    detailText: string
  }
}

export const FactorList: React.FC<FactorListProps> = ({
  title,
  factors,
  symbol,
  expandedFactors,
  onToggleFactor,
  onToggleAll,
  getFactorStatus,
  getFactorStatusStyle,
}) => {
  if (factors.length === 0) {
    return null
  }

  const categoryFactorKeys = factors.map(f => `${symbol}-${f.key}`)
  const allExpanded = categoryFactorKeys.every(key => expandedFactors.has(key))

  return (
    <div className="mb-6 last:mb-0">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-base font-light text-gray-900 dark:text-gray-100">{title}</h3>
        <button
          onClick={e => {
            e.stopPropagation()
            onToggleAll(factors, !allExpanded)
          }}
          className="rounded-lg px-3 py-1.5 text-xs font-light text-gray-600 dark:text-gray-400 transition-colors hover:bg-gray-100 dark:hover:bg-gray-700"
        >
          {allExpanded ? '收起全部' : '展开全部'}
        </button>
      </div>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
        {factors.map(factor => {
          const factorKey = `${symbol}-${factor.key}`
          const isExpanded = expandedFactors.has(factorKey)
          const factorStatus = getFactorStatus(factor)
          const statusStyle = getFactorStatusStyle(factorStatus)

          return (
            <FactorItem
              key={factor.key}
              factor={factor}
              isExpanded={isExpanded}
              statusStyle={statusStyle}
              onToggle={() => onToggleFactor(factorKey)}
            />
          )
        })}
      </div>
    </div>
  )
}

interface FactorItemProps {
  factor: FactorDetail
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
                      {signal}
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
                      {signal}
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
