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
    <div className="min-h-screen bg-white dark:bg-gray-950 transition-colors">
      <TitleBar activeTab={activeTab} onTabChange={setActiveTab} />
      {renderContent()}
    </div>
  )
}
