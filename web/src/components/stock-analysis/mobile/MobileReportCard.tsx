import { DeleteOutlined, DownOutlined, UpOutlined } from '@ant-design/icons'
import { SwipeAction, ProgressBar } from 'antd-mobile'
import { useState } from 'react'
import type { AnalysisReport, FactorDetail } from '../../../types'
import { MobileFactorList } from './MobileFactorList'

interface MobileReportCardProps {
  symbol: string
  report?: AnalysisReport
  onRemove?: () => void
}

export const MobileReportCard: React.FC<MobileReportCardProps> = ({ symbol, report, onRemove }) => {
  const [isStockExpanded, setIsStockExpanded] = useState(false)

  if (!report) {
    return (
      <div className="mx-4 mb-4 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <div className="border-b border-gray-200 bg-gray-50 px-4 py-4 dark:border-gray-700 dark:bg-gray-900/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-gray-600 dark:border-gray-600 dark:border-t-gray-300"></div>
              <h2 className="text-xl font-light text-gray-900 dark:text-gray-100">{symbol}</h2>
              <span className="text-sm text-gray-500 dark:text-gray-400">分析中...</span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const getFearGreedTheme = (index: number) => {
    if (index >= 80) {
      return {
        bg: 'bg-emerald-50 dark:bg-emerald-900/20',
        text: 'text-emerald-700 dark:text-emerald-300',
        fillColor: '#10b981',
      }
    }
    if (index >= 60) {
      return {
        bg: 'bg-emerald-50 dark:bg-emerald-900/20',
        text: 'text-emerald-600 dark:text-emerald-400',
        fillColor: '#34d399',
      }
    }
    if (index >= 40) {
      return {
        bg: 'bg-amber-50 dark:bg-amber-900/20',
        text: 'text-amber-800 dark:text-amber-300',
        fillColor: '#f59e0b',
      }
    }
    if (index >= 20) {
      return {
        bg: 'bg-rose-50 dark:bg-rose-900/20',
        text: 'text-rose-700 dark:text-rose-300',
        fillColor: '#f43f5e',
      }
    }
    return {
      bg: 'bg-rose-50 dark:bg-rose-900/20',
      text: 'text-rose-800 dark:text-rose-400',
      fillColor: '#dc2626',
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

  const technicalFactors = report.technical_factors
  const fundamentalFactors = report.fundamental_factors
  const qlibFactors = report.qlib_factors
  const fearGreedTheme = getFearGreedTheme(report.fear_greed.index)
  const emoji = getEmojiFromLabel(report.fear_greed.label)
  // const labelText = report.fear_greed.label
  //   .replace(
  //     /[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[\u{1F600}-\u{1F64F}]|[\u{1F680}-\u{1F6FF}]/gu,
  //     ''
  //   )
  //   .trim()

  // 判断是否是美股（美股通常是纯字母代码，A股是数字代码）
  const isUSStock = /^[A-Z]+$/.test(report.symbol) && !/^\d+$/.test(report.symbol)

  // 获取显示名称（美股显示 symbol，A股显示 stock_name）
  const displayName = isUSStock ? report.symbol : report.stock_name || report.symbol

  const rightActions = [
    {
      key: 'delete',
      text: '删除',
      color: 'danger',
      icon: <DeleteOutlined />,
      onClick: () => onRemove?.(),
    },
  ]

  return (
    <div className="mb-4">
      <SwipeAction rightActions={rightActions} style={{ background: 'transparent' }}>
        <div className="mx-4 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
          {/* 股票头部信息 - 可点击展开/收起 */}
          <div
            onClick={() => setIsStockExpanded(!isStockExpanded)}
            className="w-full border-b border-gray-200 bg-gray-50 px-4 py-4 text-left transition-colors active:bg-gray-100 dark:border-gray-700 dark:bg-gray-900/50 dark:active:bg-gray-800 cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {isStockExpanded ? (
                  <UpOutlined className="text-gray-400" />
                ) : (
                  <DownOutlined className="text-gray-400" />
                )}
                <div>
                  <h2 className="text-xl font-light text-gray-900 dark:text-gray-100">
                    {displayName}
                  </h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    当前价格: ${report.price.toFixed(2)}
                  </p>
                </div>
              </div>

              {/* 贪恐指数 */}
              <div className="flex items-center gap-2">
                <div className="w-20">
                  <ProgressBar
                    percent={report.fear_greed.index}
                    style={{
                      '--fill-color': fearGreedTheme.fillColor,
                      '--track-color': 'var(--color-gray-700)',
                    }}
                    rounded
                  />
                </div>
                <div className="flex flex-col items-end">
                  <span className="text-base">{emoji}</span>
                  <span className={`text-sm font-light ${fearGreedTheme.text}`}>
                    {report.fear_greed.index.toFixed(1)}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* 因子列表 - 可折叠 */}
          {isStockExpanded && (
            <div className="px-4 py-4">
              <MobileFactorList
                title={`基本面 (${fundamentalFactors.length})`}
                factors={fundamentalFactors}
                getFactorStatus={getFactorStatus}
                getFactorStatusStyle={getFactorStatusStyle}
              />

              <MobileFactorList
                title={`技术面 (${technicalFactors.length})`}
                factors={technicalFactors}
                getFactorStatus={getFactorStatus}
                getFactorStatusStyle={getFactorStatusStyle}
              />

              <MobileFactorList
                title={`Qlib因子 (${qlibFactors.length})`}
                factors={qlibFactors}
                getFactorStatus={getFactorStatus}
                getFactorStatusStyle={getFactorStatusStyle}
              />
            </div>
          )}
        </div>
      </SwipeAction>
    </div>
  )
}
