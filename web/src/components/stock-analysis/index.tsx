import { useState, useEffect } from 'react'
import { AlertTriangle } from 'lucide-react'
import { Form } from './Form'
import { ReportCard } from './ReportCard'
import { stockApi } from '../../api/client'
import type { AnalysisReport } from '../../types'

const SAVED_SYMBOLS_KEY = 'stock-analysis-saved-symbols'

export function StockAnalysis() {
  const [symbolList, setSymbolList] = useState<string[]>([])
  const [reports, setReports] = useState<Map<string, AnalysisReport>>(new Map())

  useEffect(() => {
    const loadSavedSymbols = async () => {
      try {
        const savedSymbolsStr = localStorage.getItem(SAVED_SYMBOLS_KEY)
        const _symbols = savedSymbolsStr ? JSON.parse(savedSymbolsStr) : []
        setSymbolList(_symbols)

        _symbols.forEach(async (symbol: string) => {
          const reports = await stockApi.analyzeStocks([symbol])
          if (reports.length > 0) {
            const report = reports[0]
            setReports(prev => new Map(prev).set(symbol, report))
          }
        })
      } catch (error) {
        console.error('Failed to load saved symbols:', error)
      }
    }

    loadSavedSymbols()
  }, [])

  const updateSymbolList = (symbols: string[]) => {
    setSymbolList(symbols)
    localStorage.setItem(SAVED_SYMBOLS_KEY, JSON.stringify(symbols))
  }

  const handleAddSymbol = async (symbol: string) => {
    if (symbolList.includes(symbol)) {
      return
    }

    const _symbols = [...symbolList, symbol]
    updateSymbolList(_symbols)

    if (reports.has(symbol)) {
      return
    }

    try {
      const [report] = await stockApi.analyzeStocks([symbol])
      if (report) {
        setReports(prev => new Map(prev).set(symbol, report))
      }
    } catch (err: any) {
      console.error('分析失败:', err)
    }
  }

  const handleRemoveReport = (symbol: string) => {
    // 从股票列表中移除
    const newsymbolList = symbolList.filter(s => s !== symbol)
    setSymbolList(newsymbolList)
    localStorage.setItem(SAVED_SYMBOLS_KEY, JSON.stringify(newsymbolList))
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

      {/* 分析表单 */}
      <div className="mb-8">
        <Form onAddSymbol={handleAddSymbol} />
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
              onRemove={() => handleRemoveReport(symbol)}
            />
          )
        })}
      </div>
    </div>
  )
}
