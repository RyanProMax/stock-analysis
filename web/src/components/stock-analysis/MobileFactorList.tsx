import React from 'react'
import { TrendingUp, TrendingDown, CircleSlash2 } from 'lucide-react'
import type { FactorDetail } from '../../types'

interface MobileFactorListProps {
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

export const MobileFactorList: React.FC<MobileFactorListProps> = ({
  title,
  factors,
  getFactorStatus,
  getFactorStatusStyle,
}) => {
  // 过滤出有信号的因子
  const filteredFactors = factors.filter(
    factor => factor.bullish_signals.length > 0 || factor.bearish_signals.length > 0
  )

  return (
    <div className="mb-6 last:mb-0">
      <div className="mb-4">
        <h3 className="text-base font-light text-gray-900 dark:text-gray-100">{title}</h3>
      </div>

      {filteredFactors.length ? (
        <div className="space-y-3">
          {filteredFactors.map(factor => {
            const factorStatus = getFactorStatus(factor)
            const statusStyle = getFactorStatusStyle(factorStatus)
            const hasSignals =
              factor.bullish_signals.length > 0 || factor.bearish_signals.length > 0

            return (
              <div
                key={factor.key}
                className={`overflow-hidden rounded-lg border transition-all ${
                  hasSignals
                    ? `${statusStyle.border} ${statusStyle.bg}`
                    : 'border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800'
                }`}
              >
                <div className="p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <span className={`h-2 w-2 rounded-full ${statusStyle.dot}`} />
                    <h4 className="text-sm font-light text-gray-900 dark:text-gray-100">
                      {factor.name}
                    </h4>
                  </div>

                  {/* 信号列表 */}
                  {hasSignals ? (
                    <div className="space-y-2">
                      {/* 看涨信号 */}
                      {factor.bullish_signals.map((signal, idx) => (
                        <div key={`bullish-${idx}`} className="flex items-start gap-2">
                          <TrendingUp className="h-3 w-3 text-emerald-600 dark:text-emerald-400 mt-0.5 shrink-0" />
                          <span className={`text-xs leading-relaxed ${statusStyle.detailText}`}>
                            {signal}
                          </span>
                        </div>
                      ))}

                      {/* 看跌信号 */}
                      {factor.bearish_signals.map((signal, idx) => (
                        <div key={`bearish-${idx}`} className="flex items-start gap-2">
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
          })}
        </div>
      ) : (
        <div className="text-center py-8">
          <p className="text-sm text-gray-500 dark:text-gray-400">暂无信号因子</p>
        </div>
      )}
    </div>
  )
}
