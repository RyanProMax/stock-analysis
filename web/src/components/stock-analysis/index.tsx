import { useState, useEffect } from 'react'
import { DesktopLayout } from './desktop/DesktopLayout'
import { MobileLayout } from './mobile/MobileLayout'
import { ServiceStartupProgress } from './ServiceStartupProgress'
import { stockApi } from '../../api/client'

import type { ComponentProps } from '../layout/constant'
import type { AnalysisReport } from '../../types'

const SAVED_SYMBOLS_KEY = 'stock-analysis-saved-symbols'

const genErrorReport = ({ symbol, error }: { symbol: string; error: Error }): AnalysisReport => ({
  symbol,
  stock_name: null,
  price: 0,
  technical: { factors: [], data_source: '', raw_data: null },
  fundamental: { factors: [], data_source: '', raw_data: null },
  qlib: { factors: [], data_source: '', raw_data: null },
  fear_greed: { index: 0, label: '' },
  status: 'error',
  error: error.message || '未知错误',
})

export function StockAnalysis({ isMobile }: ComponentProps) {
  const [startupProgress, setStartupProgress] = useState(0)
  const [symbolList, setSymbolList] = useState<string[]>([])
  const [reports, setReports] = useState<Map<string, AnalysisReport>>(new Map())

  useEffect(() => {
    ;(async () => {
      try {
        await stockApi.waitForService(setStartupProgress)
        const savedSymbolsStr = localStorage.getItem(SAVED_SYMBOLS_KEY)
        const _symbols = savedSymbolsStr ? JSON.parse(savedSymbolsStr) : []
        setSymbolList(_symbols)

        _symbols.forEach(async (symbol: string) => {
          try {
            const reports = await stockApi.analyzeStocks([symbol])
            if (reports.length > 0) {
              const report = reports[0]
              setReports(prev => new Map(prev).set(symbol, { ...report, status: 'success' }))
            }
          } catch (error: any) {
            console.error(`分析 ${symbol} 失败:`, error)
            setReports(prev => new Map(prev).set(symbol, genErrorReport({ symbol, error })))
          }
        })
      } catch (error) {
        console.error('初始化失败', error)
      }
    })()
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
        setReports(prev => new Map(prev).set(symbol, { ...report, status: 'success' }))
      }
    } catch (error: any) {
      console.error('分析失败:', error)
      setReports(prev => new Map(prev).set(symbol, genErrorReport({ symbol, error })))
    }
  }

  const handleRemoveReport = (symbol: string) => {
    // 从股票列表中移除
    const newsymbolList = symbolList.filter(s => s !== symbol)
    setSymbolList(newsymbolList)
    localStorage.setItem(SAVED_SYMBOLS_KEY, JSON.stringify(newsymbolList))
  }

  if (startupProgress < 100) {
    return <ServiceStartupProgress progress={startupProgress} />
  }

  return isMobile ? (
    <MobileLayout
      symbolList={symbolList}
      reports={reports}
      onAddSymbol={handleAddSymbol}
      onRemoveReport={handleRemoveReport}
    />
  ) : (
    <DesktopLayout
      symbolList={symbolList}
      reports={reports}
      onAddSymbol={handleAddSymbol}
      onRemoveReport={handleRemoveReport}
    />
  )
}
