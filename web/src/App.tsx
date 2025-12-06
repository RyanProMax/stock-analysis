import { useState, useEffect } from 'react'
import { Layout, Typography, Spin, Empty, Alert, Space } from 'antd'
import { ExclamationCircleOutlined } from '@ant-design/icons'
import { StockAnalysisForm } from './components/StockAnalysisForm'
import { StockReportCard } from './components/StockReportCard'
import { stockApi } from './api/client'
import type { AnalysisReport } from './types'
import 'antd/dist/reset.css'
import './App.css'

const { Header, Content } = Layout
const { Title, Text } = Typography

// 预设股票代码列表
const DEFAULT_SYMBOLS = ['TQQQ', 'TECL', 'NVDA', 'GOOGL', 'TSLA', 'AAPL', 'YINN', 'BABA', 'CONL']

function App() {
  const [reports, setReports] = useState<AnalysisReport[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [symbols, setSymbols] = useState<string[]>(DEFAULT_SYMBOLS)

  const fetchStockData = async (symbolList: string[]) => {
    try {
      setLoading(true)
      setError(null)
      const reports = await stockApi.analyzeStocks(symbolList)
      setReports(reports)
      if (reports.length === 0) {
        setError('未获取到任何股票数据，请检查股票代码是否正确')
      }
    } catch (err: any) {
      console.error('分析失败:', err)
      setError(err.response?.data?.detail || '分析失败，请稍后重试')
      setReports([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStockData(symbols)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleAnalysisComplete = (newReports: AnalysisReport[]) => {
    setReports(newReports)
    setError(null)
  }

  const handleSymbolsChange = (newSymbols: string[]) => {
    setSymbols(newSymbols)
    fetchStockData(newSymbols)
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{ background: '#001529', padding: '0 24px', display: 'flex', alignItems: 'center' }}
      >
        <Title level={3} style={{ color: '#fff', margin: 0 }}>
          股票分析报告
        </Title>
      </Header>
      <Content style={{ padding: '24px', background: '#f0f2f5' }}>
        <div style={{ maxWidth: 1400, margin: '0 auto' }}>
          {/* 风险提示 */}
          <Alert
            message={
              <Space>
                <ExclamationCircleOutlined />
                <Text>投资有风险，入市需谨慎。此报告仅供参考。</Text>
              </Space>
            }
            type="warning"
            showIcon
            style={{ marginBottom: 24 }}
          />

          {/* 分析表单 */}
          <StockAnalysisForm
            onAnalysisComplete={handleAnalysisComplete}
            loading={loading}
            setLoading={setLoading}
            defaultSymbols={DEFAULT_SYMBOLS}
            onSymbolsChange={handleSymbolsChange}
          />

          {/* 错误提示 */}
          {error && (
            <Alert
              message={error}
              type="error"
              showIcon
              closable
              onClose={() => setError(null)}
              style={{ marginBottom: 24 }}
            />
          )}

          {/* 加载状态 */}
          {loading && reports.length === 0 && (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <Spin size="large" tip="正在分析股票数据..." />
            </div>
          )}

          {/* 无数据提示 */}
          {!loading && reports.length === 0 && !error && (
            <Empty description="暂无股票数据" style={{ marginTop: 60 }} />
          )}

          {/* 股票报告列表 */}
          {!loading && reports.length > 0 && (
            <div>
              {reports.map(report => (
                <StockReportCard key={report.symbol} report={report} />
              ))}
            </div>
          )}
        </div>
      </Content>
    </Layout>
  )
}

export default App
