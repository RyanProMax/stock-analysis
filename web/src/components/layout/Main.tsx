import { useState } from 'react'
import { TitleBar } from './TitleBar'
import { StockAnalysis } from '../stock-analysis'

type Tab = 'stock-analysis'

export function Main() {
  const [activeTab, setActiveTab] = useState<Tab>('stock-analysis')

  const renderContent = () => {
    switch (activeTab) {
      case 'stock-analysis':
        return <StockAnalysis />
      default:
        return <StockAnalysis />
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
      <TitleBar activeTab={activeTab} onTabChange={setActiveTab} />
      {renderContent()}
    </div>
  )
}
