import { useState } from 'react'
import { AlertTriangle } from 'lucide-react'
import { Form } from './Form'
import { ReportCard } from './ReportCard'
import { stockApi } from '../../api/client'
import type { AnalysisReport } from '../../types'

export function StockAnalysis() {
  const [reports, setReports] = useState<Map<string, AnalysisReport>>(new Map())
  const [loadingSymbols, setLoadingSymbols] = useState<Set<string>>(new Set())
  const [errorMap, setErrorMap] = useState<Map<string, string>>(new Map())

  // 添加股票并自动查询报告
  const handleAddSymbol = async (symbol: string) => {
    // 如果已经存在报告，不重复查询
    if (reports.has(symbol)) {
      return
    }

    // 如果正在加载，不重复请求
    if (loadingSymbols.has(symbol)) {
      return
    }

    try {
      setLoadingSymbols(prev => new Set(prev).add(symbol))
      setErrorMap(prev => {
        const newMap = new Map(prev)
        newMap.delete(symbol)
        return newMap
      })

      const reports = await stockApi.analyzeStocks([symbol])
      if (reports.length > 0) {
        const report = reports[0]
        setReports(prev => new Map(prev).set(symbol, report))
      } else {
        setErrorMap(prev => new Map(prev).set(symbol, '未获取到股票数据，请检查股票代码是否正确'))
      }
    } catch (err: any) {
      console.error('分析失败:', err)
      setErrorMap(prev => new Map(prev).set(symbol, err.message || '分析失败，请稍后重试'))
    } finally {
      setLoadingSymbols(prev => {
        const newSet = new Set(prev)
        newSet.delete(symbol)
        return newSet
      })
    }
  }

  // 删除股票报告
  const handleRemoveReport = (symbol: string) => {
    setReports(prev => {
      const newMap = new Map(prev)
      newMap.delete(symbol)
      return newMap
    })
    setErrorMap(prev => {
      const newMap = new Map(prev)
      newMap.delete(symbol)
      return newMap
    })
  }

  // 检查是否有任何加载中的股票
  const hasLoading = loadingSymbols.size > 0
  const allReports = Array.from(reports.values())

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
        <Form onAddSymbol={handleAddSymbol} />
      </div>

      {/* 无数据提示 */}
      {!hasLoading && allReports.length === 0 && errorMap.size === 0 && (
        <div className="mb-6 text-center text-gray-500 dark:text-gray-400">
          <p>暂无股票数据，请在上方输入股票代码进行分析</p>
        </div>
      )}

      {/* 股票报告列表 */}
      <div className="space-y-3">
        {allReports.map(report => (
          <ReportCard
            key={report.symbol}
            report={report}
            onRemove={() => handleRemoveReport(report.symbol)}
          />
        ))}

        {/* 加载中的股票 */}
        {Array.from(loadingSymbols).map(symbol => (
          <ReportCard
            key={symbol}
            symbol={symbol}
            loading={true}
            onRemove={() => handleRemoveReport(symbol)}
          />
        ))}

        {/* 错误的股票 */}
        {Array.from(errorMap.entries()).map(([symbol, error]) => (
          <div
            key={symbol}
            className="rounded-xl border border-rose-200 bg-rose-50 p-4 dark:border-rose-800 dark:bg-rose-900/20"
          >
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 text-rose-700 dark:text-rose-400">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                <span className="font-medium">{symbol}</span>
                <span className="text-sm font-light">{error}</span>
              </div>
              <button
                onClick={() => handleRemoveReport(symbol)}
                className="rounded-md px-2 py-1 text-rose-600 transition-colors hover:bg-rose-100 hover:text-rose-800 dark:text-rose-400 dark:hover:bg-rose-900/30 dark:hover:text-rose-300"
                aria-label="删除"
              >
                ×
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
