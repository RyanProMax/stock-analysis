import { useState, useMemo, useEffect, useRef } from 'react'
import { Select, Button, Space } from 'antd'
import { SearchOutlined, CloseOutlined } from '@ant-design/icons'
import type { SelectProps } from 'antd'
import { stockApi } from '../../api/client'
import type { StockInfo } from '../../types'

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

  // 处理输入框回车或失焦，自动添加股票代码
  const handleBlur = () => {
    if (inputValue && !selectedSymbols.includes(inputValue)) {
      const newSymbols = [...selectedSymbols, inputValue]
      setSelectedSymbols(newSymbols)
      setInputValue('')
    }
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

  // 根据 symbol 获取股票名称
  const getStockName = (symbol: string): string => {
    const stock = stockList.find(s => s.symbol === symbol)
    return stock?.name || symbol
  }

  return (
    <div className="w-full">
      <Space.Compact className="w-full" size="middle">
        <Select
          mode="multiple"
          showSearch
          value={selectedSymbols}
          placeholder={stockListLoading ? '正在加载股票列表...' : '输入或选择股票代码（支持多选）'}
          onChange={handleChange}
          onSearch={handleSearch}
          onBlur={handleBlur}
          onInputKeyDown={handleKeyDown}
          options={options}
          filterOption={(input, option) => {
            const value = typeof option?.value === 'string' ? option.value : ''
            const label =
              typeof option?.label === 'string' ? option.label : String(option?.label || '')
            return (
              value.toUpperCase().includes(input.toUpperCase()) ||
              label.toUpperCase().includes(input.toUpperCase())
            )
          }}
          tagRender={props => {
            const { value, closable, onClose } = props
            // 显示股票名称而不是 label
            const displayName = getStockName(value as string)
            return (
              <span
                className="ant-select-selection-item"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  padding: '0 8px',
                  margin: '2px 4px 2px 0',
                  background: 'rgba(255, 255, 255, 0.08)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '4px',
                  maxWidth: '100%',
                }}
              >
                <span className="ant-select-selection-item-content" style={{ marginRight: '4px' }}>
                  {displayName}
                </span>
                {closable && (
                  <span
                    className="ant-select-selection-item-remove"
                    onClick={onClose}
                    style={{
                      cursor: 'pointer',
                      marginLeft: '6px',
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <CloseOutlined style={{ fontSize: '14px', opacity: 0.7 }} />
                  </span>
                )}
              </span>
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
          maxTagCount="responsive"
          size="large"
          disabled={loading || stockListLoading}
          className="flex-1 stock-select"
          style={{ width: '100%' }}
          notFoundContent={
            stockListLoading ? '正在加载...' : inputValue ? `按回车添加: ${inputValue}` : '暂无数据'
          }
          allowClear
        />
        <Button
          type="primary"
          icon={<SearchOutlined />}
          onClick={handleAnalyze}
          loading={loading || stockListLoading}
          disabled={loading || stockListLoading || selectedSymbols.length === 0}
          size="large"
        >
          分析
        </Button>
      </Space.Compact>
      <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
        提示：可直接输入股票代码，按回车或点击外部区域添加；支持美股（如 NVDA、AAPL）和 A股（如
        600519）
      </div>
    </div>
  )
}
