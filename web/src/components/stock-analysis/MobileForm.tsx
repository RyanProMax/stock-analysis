import { useState, useRef } from 'react'
import { Input, Button } from 'antd-mobile'

interface MobileFormProps {
  onAddSymbol: (symbol: string) => unknown
}

export const MobileForm: React.FC<MobileFormProps> = ({ onAddSymbol }) => {
  const [inputValue, setInputValue] = useState<string>('')
  const inputRef = useRef<any>(null)

  // 处理添加股票
  const handleAdd = () => {
    const symbol = inputValue.trim().toUpperCase()
    if (symbol) {
      onAddSymbol(symbol)
      setInputValue('')
    }
  }

  // 处理回车键
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleAdd()
    }
  }

  return (
    <div className="w-full">
      <div className="flex gap-3">
        <Input
          ref={inputRef}
          value={inputValue}
          onChange={value => setInputValue(value.toUpperCase())}
          onKeyDown={handleKeyDown}
          placeholder="输入股票代码（如：000001、NVDA、AAPL）"
          className="flex-1"
          style={{
            background: 'rgb(31, 41, 55)',
            borderColor: 'rgb(55, 65, 81)',
            color: 'rgb(243, 244, 246)',
            '--placeholder-color': 'rgb(156, 163, 175)',
          }}
        />
        <Button
          color="primary"
          fill="solid"
          shape="rounded"
          onClick={handleAdd}
          disabled={!inputValue.trim()}
          size="middle"
          className="px-6"
          style={{
            background: 'var(--color-primary)',
            borderColor: 'var(--color-primary)',
            color: '#ffffff',
          }}
        >
          添加
        </Button>
      </div>
    </div>
  )
}
