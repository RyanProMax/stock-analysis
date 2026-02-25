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
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(
    symbolList.length > 0 ? symbolList[0] : null
  )
  const [inputValue, setInputValue] = useState('')

  // 处理添加股票
  const handleAdd = () => {
    const symbol = inputValue.trim().toUpperCase()
    if (symbol) {
      onAddSymbol(symbol)
      setInputValue('')
      // 自动选中新添加的股票
      setSelectedSymbol(symbol)
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

  // 处理删除股票
  const handleRemoveSymbol = (symbol: string) => {
    onRemoveReport(symbol)
    // 如果删除的是当前选中的股票，清空选中状态（会自动选择列表中的第一支）
    if (selectedSymbol === symbol) {
      setSelectedSymbol(null)
    }
  }

  return (
    <div className="mx-auto max-w-[1800px] px-4 py-12 sm:px-6 lg:px-8">
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
        <Input
          value={inputValue}
          onChange={e => setInputValue(e.target.value.toUpperCase())}
          onKeyDown={handleKeyDown}
          placeholder="输入股票代码（如：000001、NVDA、AAPL）"
          size="large"
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

      {/* 主内容区 - 左右分栏 */}
      <div className="min-w-[1024px] overflow-x-auto">
        <div className="flex gap-6" style={{ minWidth: '1024px' }}>
          {/* 左侧股票列表 */}
          <StockListSidebar
            symbolList={symbolList}
            reports={reports}
            selectedSymbol={selectedSymbol}
            onSelectSymbol={handleSelectSymbol}
            onRemoveSymbol={handleRemoveSymbol}
          />

          {/* 右侧股票详情 */}
          <StockDetailPanel
            symbol={selectedSymbol}
            report={selectedSymbol ? reports.get(selectedSymbol) : undefined}
            onRemove={selectedSymbol ? () => handleRemoveSymbol(selectedSymbol) : undefined}
          />
        </div>
      </div>
    </div>
  )
}
