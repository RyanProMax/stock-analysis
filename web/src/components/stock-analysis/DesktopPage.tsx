import React, { useState } from 'react'
import { AlertTriangle } from 'lucide-react'
import { PlusOutlined } from '@ant-design/icons'
import { Input, Button } from 'antd'
import { StockListSidebar } from './desktop/StockListSidebar'
import { StockDetailPanel } from './desktop/StockDetailPanel'
import type { AnalysisReport } from '../../types'

interface DesktopPageProps {
  symbolList: string[]
  reports: Map<string, AnalysisReport>
  onAddSymbol: (symbol: string) => void
  onRemoveReport: (symbol: string) => void
}

export const DesktopPage: React.FC<DesktopPageProps> = ({
  symbolList,
  reports,
  onAddSymbol,
  onRemoveReport,
}) => {
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null)
  const [inputValue, setInputValue] = useState<string>('')

  // 处理添加股票
  const handleAdd = () => {
    const symbol = inputValue.trim().toUpperCase()
    if (symbol) {
      onAddSymbol(symbol)
      setInputValue('')
      // 自动选中新添加的股票
      if (!selectedSymbol) {
        setSelectedSymbol(symbol)
      }
    }
  }

  // 处理回车键
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleAdd()
    }
  }

  // 处理选择股票
  const handleSelectSymbol = (symbol: string) => {
    setSelectedSymbol(symbol)
  }

  // 处理移除股票
  const handleRemoveSymbol = (symbol: string) => {
    onRemoveReport(symbol)
    // 如果移除的是当前选中的股票，清空选中状态
    if (selectedSymbol === symbol) {
      setSelectedSymbol(null)
    }
  }

  return (
    <div className="min-w-[1024px] overflow-x-auto">
      {/* 顶部标题和免责声明 */}
      <div className="mb-4">
        <h1 className="text-2xl font-light text-gray-900 dark:text-gray-100">��票分析</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          本分析仅供参考，不构成投资建议
        </p>
      </div>

      {/* 风险提示 */}
      <div className="mb-6 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-800 dark:bg-amber-950/20">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
        <p className="text-sm text-amber-800 dark:text-amber-300">
          <strong>风险提示：</strong>
          股票市场有风险，投资需谨慎。本分析基于历史数据和算法模型，不保证准确性。
        </p>
      </div>

      {/* 输入表单 */}
      <div className="mb-6">
        <div className="flex gap-2">
          <Input
            value={inputValue}
            onChange={e => setInputValue(e.target.value.toUpperCase())}
            onKeyDown={handleKeyDown}
            placeholder="输入股票代码（如：000001、NVDA、AAPL）"
            size="large"
            className="flex-1"
            suffix={
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={handleAdd}
                disabled={!inputValue.trim()}
                size="small"
                className="border-0 shadow-none"
              />
            }
          />
        </div>
      </div>

      {/* 分栏视图：左侧股票列表，右侧详情面板 */}
      <div className="flex gap-4">
        <StockListSidebar
          symbolList={symbolList}
          reports={reports}
          selectedSymbol={selectedSymbol}
          onSelectSymbol={handleSelectSymbol}
          onRemoveSymbol={handleRemoveSymbol}
        />
        <StockDetailPanel
          symbol={selectedSymbol}
          report={selectedSymbol ? reports.get(selectedSymbol) : undefined}
          onRemove={() => selectedSymbol && handleRemoveSymbol(selectedSymbol)}
        />
      </div>
    </div>
  )
}
