# Desktop Layout Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 重构股票分析主页为左右分栏布局，左侧显示股票列表，右侧显示选中股票的完整分析（趋势+技术指标合并显示）

**Architecture:**
1. 根组件 `StockAnalysis` 检测屏幕宽度，<1024px 显示移动端提示，>=1024px 显示 PC 端
2. PC 端使用新的 `DesktopPage` 组件，包含顶部表单和左右分栏内容区
3. 左侧 `StockListSidebar` 固定 320px 宽，右侧 `StockDetailPanel` 最小 700px
4. 复用现有的 `TrendAnalysisTab` 和 `DesktopFactorList` 组件

**Tech Stack:** React 19, TypeScript, Tailwind CSS, Ant Design

---

## Task 1: Create MobileNotSupported Component

**Files:**
- Create: `web/src/components/stock-analysis/MobileNotSupported.tsx`

**Step 1: Create the component**

```tsx
import React from 'react'
import { Monitor } from 'lucide-react'

export const MobileNotSupported: React.FC = () => {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 dark:bg-gray-900">
      <div className="text-center">
        <Monitor className="mx-auto mb-4 h-16 w-16 text-gray-400" />
        <h1 className="mb-2 text-xl font-medium text-gray-900 dark:text-gray-100">
          暂不支持移动端
        </h1>
        <p className="text-gray-500 dark:text-gray-400">
          请使用 PC 端访问以获得更好的体验
        </p>
      </div>
    </div>
  )
}
```

**Step 2: Commit**

```bash
git add web/src/components/stock-analysis/MobileNotSupported.tsx
git commit -m "feat: add mobile not supported component"
```

---

## Task 2: Create StockListSidebar Component

**Files:**
- Create: `web/src/components/stock-analysis/desktop/StockListSidebar.tsx`

**Step 1: Create the component**

```tsx
import React from 'react'
import { X, ChevronRight } from 'lucide-react'
import type { AnalysisReport } from '../../../types'

interface StockListSidebarProps {
  symbolList: string[]
  reports: Map<string, AnalysisReport>
  selectedSymbol: string | null
  onSelectSymbol: (symbol: string) => void
  onRemoveSymbol: (symbol: string) => void
}

// 获取贪恐指数主题
const getFearGreedTheme = (index: number) => {
  if (index >= 80) return { bg: 'bg-emerald-500', ring: '#10b981' }
  if (index >= 60) return { bg: 'bg-emerald-400', ring: '#34d399' }
  if (index >= 40) return { bg: 'bg-amber-400', ring: '#f59e0b' }
  if (index >= 20) return { bg: 'bg-rose-400', ring: '#f43f5e' }
  return { bg: 'bg-rose-500', ring: '#dc2626' }
}

// 判断是否是美股
const isUSStock = (symbol: string, report?: AnalysisReport) => {
  return /^[A-Z]+$/.test(symbol) && !/^\d+$/.test(symbol)
}

// 获取显示名称
const getDisplayName = (symbol: string, report?: AnalysisReport) => {
  if (!report) return symbol
  return isUSStock(symbol) ? report.symbol : (report.stock_name || report.symbol)
}

export const StockListSidebar: React.FC<StockListSidebarProps> = ({
  symbolList,
  reports,
  selectedSymbol,
  onSelectSymbol,
  onRemoveSymbol,
}) => {
  return (
    <div className="w-80 shrink-0">
      <div
        className="space-y-2 overflow-y-auto pr-2"
        style={{ maxHeight: 'calc(100vh - 300px)' }}
      >
        {symbolList.length === 0 ? (
          <div className="flex items-center justify-center rounded-xl border border-dashed border-gray-300 bg-gray-50 px-4 py-8 text-center dark:border-gray-700 dark:bg-gray-800/60">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              暂无股票，请添加股票代码
            </p>
          </div>
        ) : (
          symbolList.map(symbol => {
            const report = reports.get(symbol)
            const displayName = getDisplayName(symbol, report)
            const isSelected = selectedSymbol === symbol
            const theme = report ? getFearGreedTheme(report.fear_greed.index) : null

            return (
              <div
                key={symbol}
                className={`group relative cursor-pointer rounded-lg border transition-all ${
                  isSelected
                    ? 'border-gray-400 bg-gray-100 dark:border-gray-600 dark:bg-gray-800'
                    : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:hover:border-gray-600 dark:hover:bg-gray-800/80'
                }`}
                onClick={() => onSelectSymbol(symbol)}
              >
                <div className="flex items-center gap-3 p-3">
                  {/* 展开/选中指示器 */}
                  <div
                    className={`shrink-0 transition-transform ${
                      isSelected ? 'rotate-90 text-gray-600 dark:text-gray-400' : 'text-gray-300 dark:text-gray-600'
                    }`}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </div>

                  {/* 股票信息 */}
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="truncate text-sm font-medium text-gray-900 dark:text-gray-100">
                        {displayName}
                      </h3>
                      {report && (
                        <span className="shrink-0 text-xs font-semibold text-gray-900 dark:text-gray-100">
                          ${report.price.toFixed(2)}
                        </span>
                      )}
                    </div>

                    {/* 贪恐指数进度条 */}
                    {report && theme && (
                      <div className="mt-1.5 flex items-center gap-2">
                        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
                          <div
                            className="h-full rounded-full transition-all duration-1000 ease-out"
                            style={{
                              width: `${report.fear_greed.index}%`,
                              backgroundColor: theme.ring,
                            }}
                          />
                        </div>
                        <span className="shrink-0 text-xs text-gray-500 dark:text-gray-400">
                          {report.fear_greed.index.toFixed(0)}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* 删除按钮 */}
                  <button
                    onClick={e => {
                      e.stopPropagation()
                      onRemoveSymbol(symbol)
                    }}
                    className="shrink-0 rounded p-1 text-gray-400 opacity-0 transition-opacity hover:bg-gray-200 hover:text-gray-600 group-hover:opacity-100 dark:hover:bg-gray-700 dark:hover:text-gray-300"
                    aria-label="删除"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
```

**Step 2: Commit**

```bash
git add web/src/components/stock-analysis/desktop/StockListSidebar.tsx
git commit -m "feat: add stock list sidebar component"
```

---

## Task 3: Create StockDetailPanel Component

**Files:**
- Create: `web/src/components/stock-analysis/desktop/StockDetailPanel.tsx`

**Step 1: Create the component**

```tsx
import React from 'react'
import { AlertCircle, FileText, X } from 'lucide-react'
import { Button } from 'antd'
import { useNavigate } from 'react-router-dom'
import { TrendAnalysisTab } from './TrendAnalysisTab'
import { FactorList } from './DesktopFactorList'
import type { AnalysisReport } from '../../../types'

interface StockDetailPanelProps {
  symbol: string | null
  report?: AnalysisReport
  onRemove?: () => void
}

// 获取贪恐指数主题
const getFearGreedTheme = (index: number) => {
  if (index >= 80) return { bg: 'bg-emerald-50 dark:bg-emerald-900/20', text: 'text-emerald-700 dark:text-emerald-300', ring: '#10b981' }
  if (index >= 60) return { bg: 'bg-emerald-50 dark:bg-emerald-900/20', text: 'text-emerald-600 dark:text-emerald-400', ring: '#34d399' }
  if (index >= 40) return { bg: 'bg-amber-50 dark:bg-amber-900/20', text: 'text-amber-800 dark:text-amber-300', ring: '#f59e0b' }
  if (index >= 20) return { bg: 'bg-rose-50 dark:bg-rose-900/20', text: 'text-rose-700 dark:text-rose-300', ring: '#f43f5e' }
  return { bg: 'bg-rose-50 dark:bg-rose-900/20', text: 'text-rose-800 dark:text-rose-400', ring: '#dc2626' }
}

// 获取 emoji 并移除
const getEmojiFromLabel = (label: string) => {
  const emojiMatch = label.match(/[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[\u{1F600}-\u{1F64F}]|[\u{1F680}-\u{1F6FF}]/u)
  return emojiMatch ? emojiMatch[0] : ''
}

const isUSStock = (symbol: string, report?: AnalysisReport) => {
  return /^[A-Z]+$/.test(symbol) && !/^\d+$/.test(symbol)
}

export const StockDetailPanel: React.FC<StockDetailPanelProps> = ({ symbol, report, onRemove }) => {
  const navigate = useNavigate()

  // 空状态
  if (!symbol) {
    return (
      <div className="flex min-w-[700px] flex-1 items-center justify-center rounded-xl border border-dashed border-gray-300 bg-gray-50 dark:border-gray-700 dark:bg-gray-800/60">
        <div className="text-center">
          <p className="text-gray-500 dark:text-gray-400">
            请从左侧列表选择股票查看详情
          </p>
        </div>
      </div>
    )
  }

  // Loading 状态
  if (!report) {
    return (
      <div className="flex min-w-[700px] flex-1 items-center justify-center rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
        <div className="flex items-center gap-3">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-gray-600 dark:border-gray-600 dark:border-t-gray-300"></div>
          <p className="text-gray-500 dark:text-gray-400">分析中...</p>
        </div>
      </div>
    )
  }

  // Error 状态
  if (report.status === 'error') {
    return (
      <div className="min-w-[700px] flex-1 rounded-xl border border-rose-200 bg-rose-50 dark:border-rose-800 dark:bg-rose-950/20">
        <div className="flex items-center gap-3 p-6">
          <AlertCircle className="h-5 w-5 shrink-0 text-rose-500" />
          <div>
            <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">分析失败</h3>
            <p className="text-sm text-rose-600 dark:text-rose-400">{report.error || '请稍后重试'}</p>
          </div>
        </div>
      </div>
    )
  }

  const fearGreedTheme = getFearGreedTheme(report.fear_greed.index)
  const emoji = getEmojiFromLabel(report.fear_greed.label)
  const labelText = report.fear_greed.label
    .replace(/[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[\u{1F600}-\u{1F64F}]|[\u{1F680}-\u{1F6FF}]/gu, '')
    .trim()
  const displayName = isUSStock(symbol) ? report.symbol : (report.stock_name || report.symbol)
  const technicalFactors = report.technical.factors
  const fundamentalFactors = report.fundamental.factors

  return (
    <div className="min-w-[700px] flex-1">
      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
        {/* 股票头部信息 */}
        <div className="border-b border-gray-200 bg-gray-50 px-6 py-4 dark:border-gray-700 dark:bg-gray-900/50">
          <div className="flex items-center justify-between">
            {/* 股票名、价格、贪恐指数 */}
            <div className="flex items-center gap-6">
              <h2 className="text-xl font-light text-gray-900 dark:text-gray-100">
                {displayName}
              </h2>
              <div className="text-left">
                <p className="text-sm text-gray-500 dark:text-gray-400">当前价格</p>
                <p className="text-base font-medium text-gray-900 dark:text-gray-100">
                  ${report.price.toFixed(2)}
                </p>
              </div>
              {/* 贪恐指数 */}
              <div className="min-w-[120px]">
                <div className="mb-1 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-base">{emoji}</span>
                    <span className={`text-sm font-light ${fearGreedTheme.text}`}>
                      {report.fear_greed.index.toFixed(1)}
                    </span>
                  </div>
                  <span className={`text-xs font-light ${fearGreedTheme.text}`}>{labelText}</span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-gray-100 dark:bg-gray-700">
                  <div
                    className="h-full rounded-full transition-all duration-1000 ease-out"
                    style={{
                      width: `${report.fear_greed.index}%`,
                      backgroundColor: fearGreedTheme.ring,
                    }}
                  />
                </div>
              </div>
            </div>

            {/* 操作按钮 */}
            <div className="flex items-center gap-2">
              <Button
                icon={<FileText className="h-4 w-4 text-white" />}
                onClick={() => navigate(`/agent/${symbol}`)}
                className="bg-gradient-to-r from-purple-500 via-pink-500 to-purple-500 bg-[length:200%_100%] bg-left text-white transition-all duration-300 hover:bg-right"
              >
                AI解读
              </Button>
              {onRemove && (
                <Button
                  icon={<X className="h-5 w-5" />}
                  onClick={onRemove}
                  type="text"
                  aria-label="删除"
                />
              )}
            </div>
          </div>
        </div>

        {/* 分析内容 */}
        <div className="p-6">
          {/* 趋势分析 */}
          {report.trend_analysis ? (
            <div className="mb-6">
              <h3 className="mb-4 text-base font-light text-gray-900 dark:text-gray-100">趋势分析</h3>
              <TrendAnalysisTab trend={report.trend_analysis} />
            </div>
          ) : null}

          {/* 技术指标 */}
          <div>
            <h3 className="mb-4 text-base font-light text-gray-900 dark:text-gray-100">技术指标</h3>
            <FactorList
              title={`技术面 (${technicalFactors.length})`}
              factors={technicalFactors}
              showAll={true}
            />
          </div>

          {/* 基本面 */}
          <div className="mt-6">
            <FactorList
              title={`基本面 (${fundamentalFactors.length})`}
              factors={fundamentalFactors}
              showAll={true}
              basic={true}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
```

**Step 2: Commit**

```bash
git add web/src/components/stock-analysis/desktop/StockDetailPanel.tsx
git commit -m "feat: add stock detail panel component"
```

---

## Task 4: Create DesktopPage Component

**Files:**
- Create: `web/src/components/stock-analysis/DesktopPage.tsx`

**Step 1: Create the component**

```tsx
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
            onRemove={() => selectedSymbol && handleRemoveSymbol(selectedSymbol)}
          />
        </div>
      </div>
    </div>
  )
}
```

**Step 2: Commit**

```bash
git add web/src/components/stock-analysis/DesktopPage.tsx
git commit -m "feat: add desktop page with split layout"
```

---

## Task 5: Update StockAnalysis Component

**Files:**
- Modify: `web/src/components/stock-analysis/index.tsx`

**Step 1: Update the component to use new layout**

```tsx
import { useState, useEffect } from 'react'
import { ServiceStartupProgress } from './ServiceStartupProgress'
import { MobileNotSupported } from './MobileNotSupported'
import { DesktopPage } from './DesktopPage'
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
  trend_analysis: null,
  status: 'error',
  error: error.message || '未知错误',
})

const PC_BREAKPOINT = 1024 // px

export function StockAnalysis({ isMobile }: ComponentProps) {
  const [startupProgress, setStartupProgress] = useState(0)
  const [symbolList, setSymbolList] = useState<string[]>([])
  const [reports, setReports] = useState<Map<string, AnalysisReport>>(new Map())
  const [isDesktopView, setIsDesktopView] = useState(false)

  // 检测屏幕宽度
  useEffect(() => {
    const checkScreenSize = () => {
      setIsDesktopView(window.innerWidth >= PC_BREAKPOINT)
    }

    checkScreenSize()
    window.addEventListener('resize', checkScreenSize)
    return () => window.removeEventListener('resize', checkScreenSize)
  }, [])

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
    const newsymbolList = symbolList.filter(s => s !== symbol)
    setSymbolList(newsymbolList)
    localStorage.setItem(SAVED_SYMBOLS_KEY, JSON.stringify(newsymbolList))
  }

  if (startupProgress < 100) {
    return <ServiceStartupProgress progress={startupProgress} />
  }

  // 移动端显示不支持提示
  if (!isDesktopView) {
    return <MobileNotSupported />
  }

  // PC端显示新布局
  return (
    <DesktopPage
      symbolList={symbolList}
      reports={reports}
      onAddSymbol={handleAddSymbol}
      onRemoveReport={handleRemoveReport}
    />
  )
}
```

**Step 2: Commit**

```bash
git add web/src/components/stock-analysis/index.tsx
git commit -m "refactor: update StockAnalysis to use new layout with mobile detection"
```

---

## Task 6: Delete Deprecated Files

**Files:**
- Delete: `web/src/components/stock-analysis/desktop/DesktopLayout.tsx`
- Delete: `web/src/components/stock-analysis/desktop/DesktopReportCard.tsx`
- Delete: `web/src/components/stock-analysis/desktop/DesktopForm.tsx`
- Delete: `web/src/components/stock-analysis/mobile/MobileLayout.tsx`
- Delete: `web/src/components/stock-analysis/mobile/MobileReportCard.tsx`
- Delete: `web/src/components/stock-analysis/mobile/MobileForm.tsx`

**Step 1: Delete the files**

```bash
rm web/src/components/stock-analysis/desktop/DesktopLayout.tsx
rm web/src/components/stock-analysis/desktop/DesktopReportCard.tsx
rm web/src/components/stock-analysis/desktop/DesktopForm.tsx
rm web/src/components/stock-analysis/mobile/MobileLayout.tsx
rm web/src/components/stock-analysis/mobile/MobileReportCard.tsx
rm web/src/components/stock-analysis/mobile/MobileForm.tsx
```

**Step 2: Commit**

```bash
git add -A
git commit -m "refactor: remove deprecated layout components"
```

---

## Task 7: Verification Testing

**Files:**
- No file changes

**Step 1: Start the dev server**

```bash
cd web
npm run dev
```

**Step 2: Manual testing checklist**

1. **PC端测试**
   - [ ] 访问页面，显示正常布局
   - [ ] 输入股票代码（如 NVDA），添加成功
   - [ ] 左侧列表显示新股票，自动选中
   - [ ] 右侧显示股票详情（趋势分析+技术指标）
   - [ ] 点击左侧其他股票，右侧正确切换
   - [ ] 点击删除按钮，股票移除
   - [ ] 删除选中股票时，右侧显示空状态

2. **移动端测试**
   - [ ] 窗口宽度 < 1024px 时显示"暂不支持移动端"
   - [ ] 窗口宽度 >= 1024px 时显示 PC 端布局
   - [ ] resize 窗口时正确切换

3. **样式测试**
   - [ ] 深色模式正常
   - [ ] 贪恐指数进度条颜色正确
   - [ ] 选中状态高亮显示
   - [ ] 水平滚动在窄屏下正常

4. **功能测试**
   - [ ] AI解读按钮跳转正确
   - [ ] localStorage 保存/恢复股票列表
   - [ ] 重复添加股票不会重复

**Step 3: Final commit if any adjustments needed**

```bash
# If any issues found and fixed:
git add -A
git commit -m "fix: [description of fix]"
```

---

## Summary

After completing all tasks:
- 4 new components created
- 1 component updated
- 6 deprecated files deleted
- New layout: left sidebar (320px) + right detail panel (min 700px)
- Mobile detection with < 1024px breakpoint
- Reuses existing TrendAnalysisTab and DesktopFactorList components
