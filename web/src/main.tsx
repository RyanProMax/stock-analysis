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
        Tag: {
          colorPrimary: '#b91c8c', // 主题主色（文案颜色）
          colorPrimaryBorder: '#b91c8c', // 边框颜色
          colorPrimaryBg: '#b91c8c', // 背景颜色
        },
      },
    }}
  >
    <App />
  </ConfigProvider>
)
