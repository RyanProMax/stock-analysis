import { createRoot } from 'react-dom/client'
import { ConfigProvider, theme } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import App from './App.tsx'
import './index.css'

// 固定暗黑模式
document.documentElement.classList.add('dark')

createRoot(document.getElementById('root')!).render(
  <ConfigProvider
    locale={zhCN}
    theme={{
      algorithm: theme.darkAlgorithm, // 使用暗色算法
      token: {
        colorPrimary: '#b91c8c',
        borderRadius: 8,
      },
      components: {
        Select: {
          // 修复 loading 时变透明的问题
          colorBgContainer: 'rgba(255, 255, 255, 0.08)',
          // 下拉菜单背景色
          colorBgElevated: 'rgba(30, 30, 30, 0.95)',
          // 禁用状态下的背景色
          colorBgContainerDisabled: 'rgba(255, 255, 255, 0.06)',
          // 选项悬停背景色
          controlItemBgHover: 'rgba(255, 255, 255, 0.08)',
          // 选项选中背景色
          controlItemBgActive: 'rgba(185, 28, 140, 0.2)',
          // 选项选中悬停背景色
          controlItemBgActiveHover: 'rgba(185, 28, 140, 0.3)',
        },
      },
    }}
  >
    <App />
  </ConfigProvider>
)
