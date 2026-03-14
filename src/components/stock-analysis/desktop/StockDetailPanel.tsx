import React from 'react'
import { AlertCircle, FileText, X } from 'lucide-react'
import { Button } from 'antd'
import { useNavigate } from 'react-router-dom'
import { TrendAnalysisTab } from './TrendAnalysisTab'
import { FactorList } from './DesktopFactorList'
import type { AnalysisReport } from '../../../types'

interface StockDetailPanelProps {
  symbol: string | null
  report?: AnalysisReport
  onRemove?: () => void
}

// 获取贪恐指数主题
const getFearGreedTheme = (index: number) => {
  if (index >= 80)
    return {
      bg: 'bg-emerald-50 dark:bg-emerald-900/20',
      text: 'text-emerald-700 dark:text-emerald-300',
      ring: '#10b981',
    }
  if (index >= 60)
    return {
      bg: 'bg-emerald-50 dark:bg-emerald-900/20',
      text: 'text-emerald-600 dark:text-emerald-400',
      ring: '#34d399',
    }
  if (index >= 40)
    return {
      bg: 'bg-amber-50 dark:bg-amber-900/20',
      text: 'text-amber-800 dark:text-amber-300',
      ring: '#f59e0b',
    }
  if (index >= 20)
    return {
      bg: 'bg-rose-50 dark:bg-rose-900/20',
      text: 'text-rose-700 dark:text-rose-300',
      ring: '#f43f5e',
    }
  return {
    bg: 'bg-rose-50 dark:bg-rose-900/20',
    text: 'text-rose-800 dark:text-rose-400',
    ring: '#dc2626',
  }
}

// 获取 emoji 并移除
const getEmojiFromLabel = (label: string) => {
  const emojiMatch = label.match(
    /[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[\u{1F600}-\u{1F64F}]|[\u{1F680}-\u{1F6FF}]/u
  )
  return emojiMatch ? emojiMatch[0] : ''
}

const isUSStock = (symbol: string) => {
  return /^[A-Z]+$/.test(symbol) && !/^\d+$/.test(symbol)
}

export const StockDetailPanel: React.FC<StockDetailPanelProps> = ({ symbol, report, onRemove }) => {
  const navigate = useNavigate()

  // 空状态
  if (!symbol) {
    return (
      <div className="flex min-w-[700px] flex-1 items-center justify-center rounded-xl border border-dashed border-gray-300 bg-gray-50 dark:border-gray-700 dark:bg-gray-800/60">
        <div className="text-center">
          <p className="text-gray-500 dark:text-gray-400">请从左侧列表选择股票查看详情</p>
        </div>
      </div>
    )
  }

  // Loading 状态
  if (!report) {
    return (
      <div className="flex min-w-[700px] flex-1 items-center justify-center rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
        <div className="flex items-center gap-3">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-gray-600 dark:border-gray-600 dark:border-t-gray-300"></div>
          <p className="text-gray-500 dark:text-gray-400">分析中...</p>
        </div>
      </div>
    )
  }

  // Error 状态
  if (report.status === 'error') {
    return (
      <div className="min-w-[700px] flex-1 rounded-xl border border-rose-200 bg-rose-50 dark:border-rose-800 dark:bg-rose-950/20">
        <div className="flex items-center gap-3 p-6">
          <AlertCircle className="h-5 w-5 shrink-0 text-rose-500" />
          <div>
            <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">分析失败</h3>
            <p className="text-sm text-rose-600 dark:text-rose-400">
              {report.error || '请稍后重试'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  const fearGreedTheme = getFearGreedTheme(report.fear_greed.index)
  const emoji = getEmojiFromLabel(report.fear_greed.label)
  const labelText = report.fear_greed.label
    .replace(
      /[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[\u{1F600}-\u{1F64F}]|[\u{1F680}-\u{1F6FF}]/gu,
      ''
    )
    .trim()
  const displayName = isUSStock(symbol) ? report.symbol : report.stock_name || report.symbol
  const technicalFactors = report.technical.factors
  const fundamentalFactors = report.fundamental.factors

  return (
    <div className="min-w-[700px] flex-1">
      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
        {/* 股票头部信息 */}
        <div className="border-b border-gray-200 bg-gray-50 px-6 py-4 dark:border-gray-700 dark:bg-gray-900/50">
          <div className="flex items-center justify-between">
            {/* 股票名、价格、贪恐指数 */}
            <div className="flex items-center gap-6">
              <h2 className="text-xl font-light text-gray-900 dark:text-gray-100">{displayName}</h2>
              <div className="text-left">
                <p className="text-sm text-gray-500 dark:text-gray-400">当前价格</p>
                <p className="text-base font-medium text-gray-900 dark:text-gray-100">
                  ${report.price.toFixed(2)}
                </p>
              </div>
              {/* 贪恐指数 */}
              <div className="min-w-[120px]">
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

            {/* 操作按钮 */}
            <div className="flex items-center gap-2">
              <Button
                icon={<FileText className="h-4 w-4 text-white" />}
                onClick={() => navigate(`/agent/${symbol}`)}
                className="bg-gradient-to-r from-purple-500 via-pink-500 to-purple-500 bg-[length:200%_100%] bg-left text-white transition-all duration-300 hover:bg-right"
              >
                AI解读
              </Button>
              {onRemove && (
                <Button
                  icon={<X className="h-5 w-5" />}
                  onClick={onRemove}
                  type="text"
                  aria-label="删除"
                />
              )}
            </div>
          </div>
        </div>

        {/* 分析内容 */}
        <div className="p-6">
          {/* 趋势分析 */}
          {report.trend_analysis ? (
            <div className="mb-6">
              <h3 className="mb-4 text-base font-light text-gray-900 dark:text-gray-100">
                趋势分析
              </h3>
              <TrendAnalysisTab trend={report.trend_analysis} />
            </div>
          ) : null}

          {/* 技术指标 */}
          <div>
            <h3 className="mb-4 text-base font-light text-gray-900 dark:text-gray-100">技术指标</h3>
            <FactorList
              title={`技术面 (${technicalFactors.length})`}
              factors={technicalFactors}
              showAll={true}
            />
          </div>

          {/* 基本面 */}
          <div className="mt-6">
            <FactorList
              title={`基本面 (${fundamentalFactors.length})`}
              factors={fundamentalFactors}
              showAll={true}
              basic={true}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
