import { useState, useMemo, useEffect, useRef } from 'react'
import { Select, Button, Tag } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import type { SelectProps } from 'antd'
import { stockApi } from '../../api/client'
import type { StockInfo } from '../../types'

import './index.css'

interface FormProps {
  loading: boolean
  defaultSymbols?: string[]
  onSymbolsChange: (symbols: string[]) => void
}

// localStorage key
const STORAGE_KEY = 'stock-analysis-selected-symbols'

export const Form: React.FC<FormProps> = ({ loading, defaultSymbols = [], onSymbolsChange }) => {
  const [stockList, setStockList] = useState<StockInfo[]>([])
  const [stockListLoading, setStockListLoading] = useState(false)
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>(() => {
    // 优先使用 localStorage 中的选择，其次使用 defaultSymbols
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        const parsed = JSON.parse(saved)
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed
        }
      }
    } catch (e) {
      console.warn('读取 localStorage 失败:', e)
    }
    return defaultSymbols
  })
  const [inputValue, setInputValue] = useState<string>('')
  const hasAutoAnalyzed = useRef(false)

  // 加载股票列表
  useEffect(() => {
    ;(async () => {
      try {
        setStockListLoading(true)
        const response = await stockApi.getStockList()
        setStockList(response.stocks || [])
      } catch (error) {
        console.error('获取股票列表失败:', error)
      } finally {
        setStockListLoading(false)
      }
    })()
  }, [])

  // 当股票列表加载完成且有选中的股票时，自动触发分析（仅初始化时执行一次）
  useEffect(() => {
    if (
      !stockListLoading &&
      stockList.length > 0 &&
      selectedSymbols.length > 0 &&
      !hasAutoAnalyzed.current
    ) {
      const timer = setTimeout(() => {
        hasAutoAnalyzed.current = true
        onSymbolsChange(selectedSymbols)
      }, 100)
      return () => clearTimeout(timer)
    }
  }, [stockListLoading, stockList.length, selectedSymbols, onSymbolsChange])

  // 保存用户选择到 localStorage
  useEffect(() => {
    if (selectedSymbols.length > 0) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(selectedSymbols))
      } catch (e) {
        console.warn('保存到 localStorage 失败:', e)
      }
    }
  }, [selectedSymbols])

  // 处理选择变化
  const handleChange = (value: string[]) => {
    setSelectedSymbols(value)
    setInputValue('')
  }

  // 处理搜索输入
  const handleSearch = (value: string) => {
    setInputValue(value.toUpperCase().trim())
  }

  // 处理分析按钮点击
  const handleAnalyze = () => {
    if (selectedSymbols.length === 0) {
      return
    }
    onSymbolsChange(selectedSymbols)
  }

  // 处理输入框失焦，自动添加股票代码（仅在用户手动输入且未选择选项时）
  const handleBlur = (e: React.FocusEvent) => {
    // 延迟执行，避免与 onChange 冲突
    setTimeout(() => {
      // 检查是否点击了下拉选项（通过检查焦点是否还在 Select 组件内）
      const relatedTarget = e.relatedTarget as HTMLElement
      const isClickingOption = relatedTarget?.closest('.ant-select-dropdown')

      // 如果点击的是下拉选项，不添加输入值
      if (isClickingOption) {
        setInputValue('')
        return
      }

      // 只有在输入值存在且未被选中时才添加
      if (inputValue && !selectedSymbols.includes(inputValue)) {
        const newSymbols = [...selectedSymbols, inputValue]
        setSelectedSymbols(newSymbols)
        setInputValue('')
      } else {
        // 清空输入值
        setInputValue('')
      }
    }, 100)
  }

  // 处理输入框回车
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && inputValue && !selectedSymbols.includes(inputValue)) {
      e.preventDefault()
      const newSymbols = [...selectedSymbols, inputValue]
      setSelectedSymbols(newSymbols)
      setInputValue('')
    }
  }

  // 生成选项列表（从 API 获取的股票列表 + 用户输入）
  const options: SelectProps['options'] = useMemo(() => {
    // 将股票列表转换为选项格式
    const stockOptions: Array<{
      value: string
      label: string
      name?: string
      market?: string
    }> = stockList.map(stock => ({
      value: stock.symbol,
      name: stock.name,
      label: `${stock.symbol} - ${stock.name}`,
      market: stock.market || undefined,
    }))

    // 如果用户输入了不在列表中的代码，添加到选项中
    if (
      inputValue &&
      !stockList.some(s => s.symbol === inputValue) &&
      !selectedSymbols.includes(inputValue)
    ) {
      stockOptions.unshift({
        value: inputValue,
        label: `${inputValue} - 自定义`,
        name: inputValue,
      })
    }

    return stockOptions
  }, [stockList, inputValue, selectedSymbols])

  // 根据 symbol 获取股票信息
  const getStockInfo = (symbol: string): StockInfo | undefined => {
    return stockList.find(s => s.symbol === symbol)
  }

  // 判断是否是美股（通过 market 字段或 symbol 格式判断）
  const isUSStock = (symbol: string): boolean => {
    const stock = getStockInfo(symbol)
    if (stock?.market === '美股') {
      return true
    }
    // 如果没有 market 信息，通过 symbol 格式判断（美股通常是纯字母，A股是数字）
    return /^[A-Z]+$/.test(symbol) && !/^\d+$/.test(symbol)
  }

  // 获取 tag 显示文本（美股显示 symbol，A股显示 name）
  const getTagDisplayText = (symbol: string): string => {
    if (isUSStock(symbol)) {
      return symbol
    }
    const stock = getStockInfo(symbol)
    return stock?.name || symbol
  }

  return (
    <div className="w-full">
      <div className="flex flex-col gap-2 sm:flex-row sm:gap-0 items-stretch">
        <Select
          mode="multiple"
          value={selectedSymbols}
          placeholder={stockListLoading ? '正在加载股票列表...' : '输入或选择股票代码（支持多选）'}
          onChange={handleChange}
          onBlur={handleBlur}
          showSearch={{
            onSearch: handleSearch,
            filterOption: (input, option) => {
              const value = typeof option?.value === 'string' ? option.value : ''
              const label =
                typeof option?.label === 'string' ? option.label : String(option?.label || '')
              return (
                value.toUpperCase().includes(input.toUpperCase()) ||
                label.toUpperCase().includes(input.toUpperCase())
              )
            },
          }}
          onInputKeyDown={handleKeyDown}
          options={options}
          tagRender={props => {
            const { value, closable, onClose } = props
            const displayText = getTagDisplayText(value as string)
            return (
              <Tag
                closable={closable}
                onClose={onClose}
                style={{
                  backgroundColor: 'var(--ant-color-primary-bg)',
                  margin: 0,
                  fontSize: 12,
                  lineHeight: 32,
                  height: 32,
                  display: 'inline-flex',
                  alignItems: 'center',
                  padding: '0 6px',
                }}
              >
                {displayText}
              </Tag>
            )
          }}
          optionRender={option => (
            <div className="flex items-center justify-between">
              <span>{option.label}</span>
              {option.data.market && (
                <span className="ml-2 text-xs text-gray-400">{option.data.market}</span>
              )}
            </div>
          )}
          maxTagCount={undefined}
          size="large"
          disabled={loading || stockListLoading}
          className="flex-1 stock-select"
          style={{ width: '100%' }}
          notFoundContent={
            stockListLoading ? '正在加载...' : inputValue ? `按回车添加: ${inputValue}` : '暂无数据'
          }
          allowClear
          styles={{
            popup: {
              root: {
                maxHeight: 300,
                overflow: 'auto',
              },
            },
          }}
        />
        <Button
          type="primary"
          icon={<SearchOutlined />}
          onClick={handleAnalyze}
          loading={loading || stockListLoading}
          disabled={loading || stockListLoading || selectedSymbols.length === 0}
          size="large"
          className="w-full sm:w-auto sm:ml-2 self-stretch sm:h-auto!"
        >
          <span className="sm:inline">分析</span>
        </Button>
      </div>
      <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
        提示：可直接输入股票代码，按回车或点击外部区域添加；支持美股（如 NVDA、AAPL）和 A股（如
        600519）
      </div>
    </div>
  )
}
