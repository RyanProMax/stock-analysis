import { useState } from 'react'
import { useMediaQuery } from 'react-responsive'

import { ConfigProvider as AntdConfigProvider, theme } from 'antd'
import { ConfigProvider as MobileConfigProvider } from 'antd-mobile'
import zhCN from 'antd/locale/zh_CN'

import { TitleBar } from './TitleBar'
import { StockAnalysis } from '../stock-analysis'
import { TabKey } from './constant'

export function Main() {
  // 使用 react-responsive 检测屏幕尺寸
  const isMobile = useMediaQuery({ maxWidth: 768 })

  const [activeTab, setActiveTab] = useState<TabKey>(TabKey.StockAnalysis)

  const renderContent = () => {
    switch (activeTab) {
      case TabKey.StockAnalysis:
        return <StockAnalysis isMobile={isMobile} />
      default:
        return <StockAnalysis isMobile={isMobile} />
    }
  }

  return (
    <AntdConfigProvider
      locale={zhCN}
      theme={{
        algorithm: theme.darkAlgorithm, // 使用暗色算法
        token: {
          colorPrimary: '#b91c8c',
          borderRadius: 8,
        },
        components: {
          Tag: {
            colorPrimary: '#b91c8c', // 主题主色（文案颜色）
            colorPrimaryBorder: '#b91c8c', // 边框颜色
            colorPrimaryBg: '#b91c8c', // 背景颜色
          },
        },
      }}
    >
      <MobileConfigProvider>
        <div className="min-h-screen bg-white dark:bg-gray-950 transition-colors">
          <TitleBar activeTab={activeTab} onTabChange={setActiveTab} />
          {renderContent()}
        </div>
      </MobileConfigProvider>
    </AntdConfigProvider>
  )
}
