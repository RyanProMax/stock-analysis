import { useState, useEffect } from 'react'
import { Search } from 'lucide-react'
import { stockApi } from '../../api/client'
import type { AnalysisReport } from '../../types'

interface FormProps {
  onAnalysisComplete: (reports: AnalysisReport[]) => void
  loading: boolean
  setLoading: (loading: boolean) => void
  defaultSymbols?: string[]
  onSymbolsChange?: (symbols: string[]) => void
}

export const Form: React.FC<FormProps> = ({
  onAnalysisComplete,
  loading,
  setLoading,
  defaultSymbols = [],
  onSymbolsChange,
}) => {
  const [inputValue, setInputValue] = useState(defaultSymbols.join(', '))

  useEffect(() => {
    if (defaultSymbols.length > 0) {
      setInputValue(defaultSymbols.join(', '))
    }
  }, [defaultSymbols])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const symbols = inputValue
      .split(/[,，\s]+/)
      .map(s => s.trim().toUpperCase())
      .filter(s => s.length > 0)

    if (symbols.length === 0) {
      alert('请输入至少一个股票代码')
      return
    }

    setLoading(true)
    try {
      const reports = await stockApi.analyzeStocks(symbols)
      if (reports.length === 0) {
        alert('未获取到任何股票数据，请检查股票代码是否正确')
      } else {
        onAnalysisComplete(reports)
        if (onSymbolsChange) {
          onSymbolsChange(symbols)
        }
      }
    } catch (error: any) {
      console.error('分析失败:', error)
      alert(error.response?.data?.detail || '分析失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mb-6 flex gap-2">
      <input
        type="text"
        value={inputValue}
        onChange={e => setInputValue(e.target.value)}
        placeholder="输入股票代码，多个代码用逗号或空格分隔（如：NVDA, AAPL, 600519）"
        disabled={loading}
        className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 dark:focus:border-blue-400"
      />
      <button
        type="submit"
        disabled={loading}
        className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50 dark:bg-blue-500 dark:hover:bg-blue-600"
      >
        {loading ? (
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
        ) : (
          <Search className="h-4 w-4" />
        )}
        <span>分析</span>
      </button>
    </form>
  )
}
