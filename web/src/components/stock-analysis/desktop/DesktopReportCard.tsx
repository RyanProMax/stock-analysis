import { X, ChevronDown, ChevronUp, AlertCircle, FileText } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from 'antd'
import type { AnalysisReport, FactorDetail } from '../../../types'
import { FactorList } from './DesktopFactorList'

interface ReportCardProps {
  symbol: string
  report?: AnalysisReport
  onRemove?: () => void
}

export const ReportCard: React.FC<ReportCardProps> = ({ symbol, report, onRemove }) => {
  const [isStockExpanded, setIsStockExpanded] = useState(false)
  const [isHovered, setIsHovered] = useState(false)
  const navigate = useNavigate()

  if (!report) {
    return (
      <div
        className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <div className="border-b border-gray-200 bg-gray-50 px-4 py-4 sm:px-6 dark:border-gray-700 dark:bg-gray-900/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-gray-600 dark:border-gray-600 dark:border-t-gray-300"></div>
              <h2 className="w-[100px] truncate text-xl font-light text-gray-900 dark:text-gray-100">
                {symbol}
              </h2>
              <span className="text-sm text-gray-500 dark:text-gray-400">分析中...</span>
            </div>
            {onRemove && (
              <button
                onClick={onRemove}
                className={`rounded-md p-1 text-gray-400 transition-all duration-200 hover:bg-gray-200 hover:text-gray-600 dark:hover:bg-gray-700 dark:hover:text-gray-300 ${
                  isHovered ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-2'
                }`}
                aria-label="删除"
              >
                <X className="h-5 w-5" />
              </button>
            )}
          </div>
        </div>
      </div>
    )
  } else if (report.status === 'error') {
    return (
      <div
        className="overflow-hidden rounded-xl border border-rose-200 bg-white shadow-sm dark:border-rose-800 dark:bg-gray-800"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <div className="border-b border-rose-200 bg-rose-50 px-4 py-4 sm:px-6 dark:border-rose-800 dark:bg-rose-950/20">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <AlertCircle className="h-5 w-5 text-rose-500" />
              <h2 className="w-[100px] truncate text-xl font-light text-gray-900 dark:text-gray-100">
                {symbol}
              </h2>
              <span className="text-sm text-rose-600 dark:text-rose-400">
                {report.error || '分析失败，请稍后重试'}
              </span>
            </div>

            {onRemove && (
              <button
                onClick={onRemove}
                className={`rounded-md p-1 text-gray-400 transition-all duration-200 hover:bg-gray-200 hover:text-gray-600 dark:hover:bg-gray-700 dark:hover:text-gray-300 ${
                  isHovered ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-2'
                }`}
                aria-label="删除"
              >
                <X className="h-5 w-5" />
              </button>
            )}
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
    <div
      className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm transition-shadow hover:shadow-md dark:border-gray-700 dark:bg-gray-800"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* 股票头部信息 - 可点击展开/收起 */}
      <div
        onClick={() => setIsStockExpanded(!isStockExpanded)}
        className="w-full border-b border-gray-200 bg-gray-50 px-4 py-4 text-left transition-colors hover:bg-gray-100 sm:px-6 dark:border-gray-700 dark:bg-gray-900/50 dark:hover:bg-gray-800 cursor-pointer"
      >
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
          {/* 移动端：股票名、当前价格、贪恐指数并排一行 */}
          <div
            className={`flex items-center gap-3 sm:gap-4 transition-all duration-200 ${isHovered ? 'sm:-mr-8' : ''}`}
          >
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
          <div className="ml-auto flex items-center">
            <div
              className={`hidden min-w-[120px] sm:block transition-all duration-200 ${isHovered ? '-translate-x-2' : ''}`}
            >
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
            {/* Agent解读按钮 */}
            <div
              className={`flex items-center gap-2 transition-all duration-200 ${
                isHovered ? 'ml-2' : 'ml-0'
              }`}
            >
              <Button
                icon={<FileText className="h-4 w-4 text-white!" />}
                onClick={e => {
                  e.stopPropagation()
                  navigate(`/agent/${symbol}`)
                }}
                className={`
                  text-white overflow-hidden
                  transition-all duration-300!
                  bg-linear-to-r! from-purple-500 via-pink-500 to-purple-500
                  bg-size-[200%_100%] bg-left
                  hover:bg-right
                  ${
                    isHovered
                      ? 'opacity-100 translate-x-0 w-auto'
                      : 'opacity-0 translate-x-2 w-0 p-0!'
                  }`}
                title="查看AI解读报告"
              >
                <span className="font-medium whitespace-nowrap text-white">AI解读</span>
              </Button>
              {onRemove && (
                <Button
                  icon={<X className="h-5 w-5" />}
                  onClick={e => {
                    e.stopPropagation()
                    onRemove()
                  }}
                  className={`
                    overflow-hidden
                    rounded-md transition-all duration-300!
                    ${isHovered ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-2 w-0'}`}
                  type="text"
                  aria-label="删除"
                />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 因子列表 - 可折叠 */}
      {isStockExpanded && (
        <div className="p-4 sm:p-6">
          <FactorList
            title={`基本面 (${fundamentalFactors.length})`}
            factors={fundamentalFactors}
            getFactorStatus={getFactorStatus}
            getFactorStatusStyle={getFactorStatusStyle}
          />

          <FactorList
            title={`技术面 (${technicalFactors.length})`}
            factors={technicalFactors}
            getFactorStatus={getFactorStatus}
            getFactorStatusStyle={getFactorStatusStyle}
          />

          <FactorList
            title={`Qlib因子 (${qlibFactors.length})`}
            factors={qlibFactors}
            getFactorStatus={getFactorStatus}
            getFactorStatusStyle={getFactorStatusStyle}
          />
        </div>
      )}
    </div>
  )
}
