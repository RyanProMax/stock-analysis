import React, { useState } from 'react'
import { TrendingUp, TrendingDown, CircleSlash2 } from 'lucide-react'
import { Empty } from 'antd'
import type { FactorDetail } from '../../../types'

interface FactorListProps {
  title: string
  factors: FactorDetail[]
  showAll?: boolean
}

// 因子状态计算
const getFactorStatus = (factor: FactorDetail): 'bullish' | 'bearish' | 'neutral' => {
  const bullishCount = factor.bullish_signals.length
  const bearishCount = factor.bearish_signals.length
  if (bullishCount > bearishCount) return 'bullish'
  if (bearishCount > bullishCount) return 'bearish'
  return 'neutral'
}

// 因子状态样式
const getFactorStatusStyle = (
  status: 'bullish' | 'bearish' | 'neutral'
): {
  bg: string
  text: string
  border: string
  dot: string
  detailBg: string
  detailText: string
} => {
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

export const FactorList: React.FC<FactorListProps> = ({ title, factors, showAll = false }) => {
  const [isFilter, setIsFilter] = useState(true)

  // 过滤因子
  const filteredFactors =
    isFilter && !showAll
      ? factors.filter(
          factor => factor.bullish_signals.length > 0 || factor.bearish_signals.length > 0
        )
      : factors

  return (
    <div className="mb-6 last:mb-0">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-base font-light text-gray-900 dark:text-gray-100">{title}</h3>
        {!showAll && (
          <button
            onClick={e => {
              e.stopPropagation()
              setIsFilter(v => !v)
            }}
            className="rounded-lg px-3 py-1.5 text-xs font-light text-gray-600 dark:text-gray-400 transition-colors hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            {isFilter ? '展示全部' : '筛选信号'}
          </button>
        )}
      </div>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
        {filteredFactors.length ? (
          filteredFactors.map(factor => {
            const factorStatus = getFactorStatus(factor)
            const statusStyle = getFactorStatusStyle(factorStatus)
            const hasSignals =
              factor.bullish_signals.length > 0 || factor.bearish_signals.length > 0

            return (
              <FactorItem
                key={factor.key}
                factor={factor}
                statusStyle={statusStyle}
                hasSignals={hasSignals}
              />
            )
          })
        ) : (
          <div className="col-span-full flex justify-center">
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={
                <span className="text-gray-600 dark:text-black text-sm">暂无信号因子</span>
              }
              style={{
                height: 60,
                marginBottom: 16,
                filter: 'invert(0.7)',
              }}
              className="dark:invert"
            />
          </div>
        )}
      </div>
    </div>
  )
}

interface FactorItemProps {
  factor: FactorDetail
  statusStyle: {
    bg: string
    text: string
    border: string
    dot: string
    detailBg: string
    detailText: string
  }
  hasSignals: boolean
}

const FactorItem: React.FC<FactorItemProps> = ({ factor, statusStyle, hasSignals }) => {
  return (
    <div
      className={`overflow-hidden rounded-lg border transition-all ${
        hasSignals
          ? `${statusStyle.border} ${statusStyle.bg}`
          : 'border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800'
      }`}
    >
      <div className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <span className={`h-2 w-2 rounded-full ${statusStyle.dot}`} />
          <h4 className="text-sm font-light text-gray-900 dark:text-gray-100">{factor.name}</h4>
        </div>

        {/* 信号列表或状态描述 */}
        {hasSignals ? (
          <div className="space-y-2">
            {/* 看涨信号 */}
            {factor.bullish_signals.map((signal, idx) => (
              <div key={`bullish-${idx}`} className="flex items-center gap-2">
                <TrendingUp className="h-3 w-3 text-emerald-600 dark:text-emerald-400 mt-0.5 shrink-0" />
                <span className={`text-xs leading-relaxed ${statusStyle.detailText}`}>
                  {signal}
                </span>
              </div>
            ))}

            {/* 看跌信号 */}
            {factor.bearish_signals.map((signal, idx) => (
              <div key={`bearish-${idx}`} className="flex items-center gap-2">
                <TrendingDown className="h-3 w-3 text-rose-600 dark:text-rose-400 mt-0.5 shrink-0" />
                <span className={`text-xs leading-relaxed ${statusStyle.detailText}`}>
                  {signal}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <CircleSlash2 className="h-3 w-3 text-gray-500 dark:text-gray-400 mt-0.5 shrink-0" />
            <span className={`text-xs leading-relaxed text-gray-600 dark:text-gray-400`}>
              {factor.status || '-'}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
