import { AlertTriangle } from 'lucide-react'
import { MobileForm } from '../MobileForm'
import { MobileReportCard } from '../MobileReportCard'
import type { AnalysisReport } from '../../../types'

interface MobileLayoutProps {
  symbolList: string[]
  reports: Map<string, AnalysisReport>
  onAddSymbol: (symbol: string) => void
  onRemoveReport: (symbol: string) => void
}

export function MobileLayout({
  symbolList,
  reports,
  onAddSymbol,
  onRemoveReport,
}: MobileLayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* 顶部固定区域 */}
      <div className="sticky top-0 z-10 bg-white dark:bg-gray-800 shadow-sm">
        {/* 标题 */}
        <div className="px-4 pt-8 pb-2">
          <h1
            className="font-light tracking-tight text-gray-900 dark:text-gray-100"
            style={{ fontSize: '1.5rem' }}
          >
            股票分析报告
          </h1>
        </div>

        {/* 风险提示 */}
        <div className="px-4 pb-4">
          <div className="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400">
            <AlertTriangle className="h-3.5 w-3.5" />
            <span>投资有风险，入市需谨慎。此报告仅供参考。</span>
          </div>
        </div>

        {/* 分析表单 */}
        <div className="border-t border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-4">
          <MobileForm onAddSymbol={onAddSymbol} />
        </div>
      </div>

      {/* 内容区域 */}
      <div className="mt-6 pb-8">
        {/* 无数据提示 */}
        {symbolList.length === 0 && (
          <div className="mt-8 text-center text-gray-500 dark:text-gray-400">
            <p>暂无股票数据，请在上方输入股票代码进行分析</p>
          </div>
        )}

        {/* 股票卡片列表 */}
        {symbolList.map(symbol => {
          const report = reports.get(symbol)

          return (
            <MobileReportCard
              key={symbol}
              symbol={symbol}
              report={report}
              onRemove={() => onRemoveReport(symbol)}
            />
          )
        })}
      </div>
    </div>
  )
}
