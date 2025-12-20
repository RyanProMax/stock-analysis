import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider as AntdConfigProvider, theme } from 'antd'
import { ConfigProvider as MobileConfigProvider } from 'antd-mobile'

import zhCN from 'antd/locale/zh_CN'

import { PageRouter } from './PageRouter'

export const Main = () => {
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
        <BrowserRouter>
          <PageRouter />
        </BrowserRouter>
      </MobileConfigProvider>
    </AntdConfigProvider>
  )
}
