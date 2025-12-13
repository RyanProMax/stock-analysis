import { useState, useEffect } from 'react'
import { DesktopLayout } from './desktop/DesktopLayout'
import { MobileLayout } from './mobile/MobileLayout'
import { stockApi } from '../../api/client'

import type { ComponentProps } from '../layout/constant'
import type { AnalysisReport } from '../../types'

const SAVED_SYMBOLS_KEY = 'stock-analysis-saved-symbols'

export function StockAnalysis({ isMobile }: ComponentProps) {
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
