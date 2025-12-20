import { useMemo } from 'react'
import { useMediaQuery } from 'react-responsive'
import { Routes, Route, useLocation, useNavigate } from 'react-router-dom'

import { TitleBar } from './TitleBar'
import { StockAnalysis } from '../stock-analysis'
import { AgentReport } from '../agent-report'
import { TabKey } from './constant'

export const PageRouter = () => {
  // 使用 react-responsive 检测屏幕尺寸
  const isMobile = useMediaQuery({ maxWidth: 768 })
  const location = useLocation()
  const navigate = useNavigate()

  const activeTab = useMemo<TabKey>(() => {
    switch (location.pathname) {
      default:
        return TabKey.StockAnalysis
    }
  }, [location.pathname])

  // 处理 tab 切换
  const handleTabChange = (tab: TabKey) => {
    switch (tab) {
      default:
        navigate('/')
        break
    }
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950 transition-colors">
      <TitleBar activeTab={activeTab} onTabChange={handleTabChange} />

      <Routes>
        <Route path="/" element={<StockAnalysis isMobile={isMobile} />} />
        <Route path="/agent/:symbol" element={<AgentReport />} />
        <Route path="*" element={<StockAnalysis isMobile={isMobile} />} />
      </Routes>
    </div>
  )
}
