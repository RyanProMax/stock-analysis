import { AlertTriangle } from 'lucide-react'
import { Form } from './DesktopForm'
import { ReportCard } from './DesktopReportCard'
import type { AnalysisReport } from '../../../types'

interface DesktopLayoutProps {
  symbolList: string[]
  reports: Map<string, AnalysisReport>
  onAddSymbol: (symbol: string) => void
  onRemoveReport: (symbol: string) => void
}

export function DesktopLayout({
  symbolList,
  reports,
  onAddSymbol,
  onRemoveReport,
}: DesktopLayoutProps) {
  return (
    <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6 lg:px-8">
      {/* 标题 */}
      <div className="mb-2 text-center">
        <h1
          className="font-light tracking-tight text-gray-900 dark:text-gray-100"
          style={{ fontSize: '1.5rem' }}
        >
          股票分析报告
        </h1>
      </div>

      {/* 风险提示 */}
      <div className="mb-8 flex items-center justify-center gap-1.5 text-center text-sm text-gray-500 dark:text-gray-400">
        <AlertTriangle className="h-3.5 w-3.5" />
        <p>投资有风险，入市需谨慎。此报告仅供参考。</p>
      </div>

      {/* 分析表单 */}
      <div className="mb-8">
        <Form onAddSymbol={onAddSymbol} />
      </div>

      {/* 无数据提示 */}
      {symbolList.length === 0 && (
        <div className="mb-6 text-center text-gray-500 dark:text-gray-400">
          <p>暂无股票数据，请在上方输入股票代码进行分析</p>
        </div>
      )}

      {/* 股票卡片列表 */}
      <div className="space-y-3">
        {symbolList.map(symbol => {
          const report = reports.get(symbol)

          return (
            <ReportCard
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
