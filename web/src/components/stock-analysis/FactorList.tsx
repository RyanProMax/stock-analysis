import React, { useState } from 'react'
import { TrendingUp, TrendingDown, CircleSlash2 } from 'lucide-react'
import { Empty } from 'antd'
import type { FactorDetail } from '../../types'

interface FactorListProps {
  title: string
  factors: FactorDetail[]
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
  getFactorStatus,
  getFactorStatusStyle,
}) => {
  const [showOnlySignals, setShowOnlySignals] = useState(true) // 默认只显示信号因子

  // 过滤因子
  const filteredFactors = showOnlySignals
    ? factors.filter(
        factor => factor.bullish_signals.length > 0 || factor.bearish_signals.length > 0
      )
    : factors

  return (
    <div className="mb-6 last:mb-0">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-base font-light text-gray-900 dark:text-gray-100">{title}</h3>
        <button
          onClick={e => {
            e.stopPropagation()
            setShowOnlySignals(v => !v)
          }}
          className="rounded-lg px-3 py-1.5 text-xs font-light text-gray-600 dark:text-gray-400 transition-colors hover:bg-gray-100 dark:hover:bg-gray-700"
        >
          {showOnlySignals ? '展示全部' : '筛选信号'}
        </button>
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
