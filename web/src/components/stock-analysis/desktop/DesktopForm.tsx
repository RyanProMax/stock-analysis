import { useState, useRef } from 'react'
import { Input, Button } from 'antd'
import { PlusOutlined } from '@ant-design/icons'

import './index.css'

interface FormProps {
  onAddSymbol: (symbol: string) => unknown
}

export const Form: React.FC<FormProps> = ({ onAddSymbol }) => {
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
      <div className="flex gap-2">
        <Input
          ref={inputRef}
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
  )
}
