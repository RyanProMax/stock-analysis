import { useState, useMemo } from 'react'
import { Select, Button, Space } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import type { SelectProps } from 'antd'

interface FormProps {
  loading: boolean
  defaultSymbols?: string[]
  onSymbolsChange: (symbols: string[]) => void
}

// 常用股票代码列表（美股 + A股）
const POPULAR_STOCKS: Array<{ value: string; label: string; market: string }> = [
  // 美股科技股
  { value: 'NVDA', label: 'NVDA - NVIDIA', market: '美股' },
  { value: 'AAPL', label: 'AAPL - Apple', market: '美股' },
  { value: 'MSFT', label: 'MSFT - Microsoft', market: '美股' },
  { value: 'GOOGL', label: 'GOOGL - Alphabet', market: '美股' },
  { value: 'AMZN', label: 'AMZN - Amazon', market: '美股' },
  { value: 'TSLA', label: 'TSLA - Tesla', market: '美股' },
  { value: 'META', label: 'META - Meta', market: '美股' },
  { value: 'NFLX', label: 'NFLX - Netflix', market: '美股' },
  // 美股ETF
  { value: 'TQQQ', label: 'TQQQ - ProShares UltraPro QQQ', market: '美股' },
  { value: 'TECL', label: 'TECL - Direxion Daily Technology Bull 3X', market: '美股' },
  { value: 'YINN', label: 'YINN - Direxion Daily FTSE China Bull 3X', market: '美股' },
  { value: 'CONL', label: 'CONL - GraniteShares 2x Long COIN Daily', market: '美股' },
  // 中概股
  { value: 'BABA', label: 'BABA - Alibaba', market: '美股' },
  { value: 'JD', label: 'JD - JD.com', market: '美股' },
  { value: 'PDD', label: 'PDD - Pinduoduo', market: '美股' },
  // A股
  { value: '600519', label: '600519 - 贵州茅台', market: 'A股' },
  { value: '000001', label: '000001 - 平安银行', market: 'A股' },
  { value: '000002', label: '000002 - 万科A', market: 'A股' },
  { value: '600036', label: '600036 - 招商银行', market: 'A股' },
  { value: '600000', label: '600000 - 浦发银行', market: 'A股' },
  { value: '000858', label: '000858 - 五粮液', market: 'A股' },
  { value: '002415', label: '002415 - 海康威视', market: 'A股' },
  { value: '300059', label: '300059 - 东方财富', market: 'A股' },
]

export const Form: React.FC<FormProps> = ({ loading, defaultSymbols = [], onSymbolsChange }) => {
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>(() => defaultSymbols)
  const [inputValue, setInputValue] = useState<string>('')

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

  // 生成选项列表（包含预设和用户输入）
  const options: SelectProps['options'] = useMemo(() => {
    const popularOptions: Array<{ value: string; label: string; market?: string }> =
      POPULAR_STOCKS.map(stock => ({
        value: stock.value,
        label: stock.label,
        market: stock.market,
      }))

    // 如果用户输入了不在预设列表中的代码，添加到选项中
    if (
      inputValue &&
      !POPULAR_STOCKS.some(s => s.value === inputValue) &&
      !selectedSymbols.includes(inputValue)
    ) {
      popularOptions.unshift({
        value: inputValue,
        label: `${inputValue} - 自定义`,
      })
    }

    return popularOptions
  }, [inputValue, selectedSymbols])

  return (
    <div className="w-full">
      <Space.Compact className="w-full" size="middle">
        <Select
          mode="multiple"
          showSearch
          value={selectedSymbols}
          placeholder="输入或选择股票代码（支持多选）"
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
          disabled={loading}
          className="flex-1 stock-select"
          style={{ width: '100%' }}
          notFoundContent={inputValue ? `按回车添加: ${inputValue}` : '暂无数据'}
          allowClear
        />
        <Button
          type="primary"
          icon={<SearchOutlined />}
          onClick={handleAnalyze}
          loading={loading}
          size="large"
          disabled={selectedSymbols.length === 0}
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
