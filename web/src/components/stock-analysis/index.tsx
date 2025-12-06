import { useState, useEffect } from 'react'
import { AlertTriangle } from 'lucide-react'
import { Form } from './Form'
import { ReportCard } from './ReportCard'
import { stockApi } from '../../api/client'
import type { AnalysisReport } from '../../types'

export function StockAnalysis() {
  const [reports, setReports] = useState<AnalysisReport[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [symbols, setSymbols] = useState<string[]>([])

  const fetchStockData = async (symbolList: string[]) => {
    try {
      setLoading(true)
      setError(null)
      const reports = await stockApi.analyzeStocks(symbolList)
      setReports(reports)
      if (reports.length === 0) {
        setError('未获取到任何股票数据，请检查股票代码是否正确')
      }
    } catch (err: any) {
      console.error('分析失败:', err)
      setError(err.message || '分析失败，请稍后重试')
      setReports([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (symbols.length > 0) {
      fetchStockData(symbols)
    } else {
      // 清空报告
      setReports([])
      setError(null)
    }
  }, [symbols])

  const handleSymbolsChange = (newSymbols: string[]) => {
    setSymbols(newSymbols)
  }

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

      {/* 分析表单 - 移到报告上方 */}
      <div className="mb-8">
        <Form loading={loading} onSymbolsChange={handleSymbolsChange} />
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="mb-6 rounded-lg border border-rose-200 bg-rose-50 p-4 dark:border-rose-800 dark:bg-rose-900/20">
          <div className="flex items-center gap-2 text-rose-700 dark:text-rose-400">
            <AlertTriangle className="h-4 w-4" />
            <p className="text-sm font-light">{error}</p>
          </div>
        </div>
      )}

      {/* 加载状态 */}
      {loading && reports.length === 0 && (
        <div className="mb-6 text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-b-2 border-gray-900 dark:border-gray-100"></div>
          <p className="mt-4 text-gray-500 dark:text-gray-400">加载中...</p>
        </div>
      )}

      {/* 无数据提示 */}
      {!loading && reports.length === 0 && !error && (
        <div className="mb-6 text-center text-gray-500 dark:text-gray-400">
          <p>暂无股票数据，请在上方输入股票代码进行分析</p>
        </div>
      )}

      {/* 股票列表 */}
      {!loading && reports.length > 0 && (
        <div className="space-y-3">
          {reports.map(report => (
            <ReportCard key={report.symbol} report={report} />
          ))}
        </div>
      )}
    </div>
  )
}
