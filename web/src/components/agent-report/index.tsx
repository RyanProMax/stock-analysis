import { useParams } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { Spin, Card, Typography, Space, Tag } from 'antd'
import {
  TrendingUp,
  CheckCircle,
  AlertCircle,
  Clock,
  BarChart3,
  Activity,
  Brain,
} from 'lucide-react'
import { stockApi } from '../../api/client'
import type { AgentReportMessage } from '../../types'

const { Title, Text, Paragraph } = Typography

export function AgentReport() {
  const { symbol } = useParams<{ symbol: string }>()
  const [messages, setMessages] = useState<AgentReportMessage[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [isComplete, setIsComplete] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const startAnalysis = () => {
    if (!symbol) return

    // Reset state
    setMessages([])
    setIsConnected(true)
    setIsComplete(false)
    setError(null)

    const eventSource = stockApi.getAgentReport(symbol, data => {
      setMessages(prev => [...prev, data])

      if (data.status === 'completed') {
        setIsComplete(true)
        setIsConnected(false)
      } else if (data.status === 'error') {
        setError(data.error || '分析出错')
        setIsConnected(false)
      }
    })

    // Cleanup on unmount
    return () => {
      eventSource.close()
    }
  }

  useEffect(() => {
    if (symbol) {
      const timer = setTimeout(() => {
        const cleanup = startAnalysis()
        return cleanup
      }, 0)
      return () => clearTimeout(timer)
    }
  }, [symbol])

  const getNodeIcon = (node: string) => {
    switch (node) {
      case 'data_fetcher':
        return <Clock className="h-5 w-5 text-blue-500" />
      case 'fundamental':
        return <TrendingUp className="h-5 w-5 text-green-500" />
      case 'technical':
        return <BarChart3 className="h-5 w-5 text-purple-500" />
      case 'qlib':
        return <Activity className="h-5 w-5 text-orange-500" />
      case 'decision':
        return <Brain className="h-5 w-5 text-pink-500" />
      default:
        return <CheckCircle className="h-5 w-5 text-gray-500" />
    }
  }

  const getNodeStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'processing'
      case 'completed':
        return 'success'
      case 'error':
        return 'error'
      default:
        return 'default'
    }
  }

  const formatContent = (content: string) => {
    // 格式化内容，处理换行和特殊标记
    return content
      .replace(/\n/g, '<br />')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(
        /```(.*?)```/gs,
        '<pre class="bg-gray-100 dark:bg-gray-800 p-3 rounded-md mt-2 mb-2"><code>$1</code></pre>'
      )
  }

  return (
    <div className="bg-gray-50 dark:bg-gray-950 transition-colors">
      <div className="container mx-auto px-4 py-6 max-w-6xl flex flex-col items-center">
        {/* Header */}
        <Title level={2} className="mt-6 font-light!">
          {symbol}
        </Title>

        {/* Error State */}
        {error && (
          <Card className="mb-6 border-rose-200 bg-rose-50 dark:border-rose-800 dark:bg-rose-950/20">
            <div className="flex items-center gap-3">
              <AlertCircle className="h-6 w-6 text-rose-500" />
              <div>
                <Text strong className="text-rose-700 dark:text-rose-300">
                  分析失败
                </Text>
                <div className="text-rose-600 dark:text-rose-400 mt-1">{error}</div>
              </div>
            </div>
          </Card>
        )}

        {/* Progress Indicators */}
        <div className="w-full mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
          {['data_fetcher', 'fundamental', 'technical', 'qlib', 'decision'].map(node => {
            const nodeMessage = messages.find(m => m.node === node)
            const isActive = nodeMessage?.status === 'running'
            const isCompleted = nodeMessage?.status === 'completed'

            return (
              <Card
                key={node}
                size="small"
                className={`text-center transition-all duration-300 ${
                  isActive
                    ? 'border-blue-300 bg-blue-50 dark:border-blue-700 dark:bg-blue-950/20'
                    : isCompleted
                      ? 'border-green-300 bg-green-50 dark:border-green-700 dark:bg-green-950/20'
                      : 'border-gray-200 dark:border-gray-700'
                }`}
              >
                <Space className="flex flex-col gap-2" size="small">
                  {getNodeIcon(node)}
                  <Text strong className="capitalize">
                    {node.replace('_', ' ')}
                  </Text>
                  <Tag color={getNodeStatusColor(nodeMessage?.status || 'pending')}>
                    {nodeMessage?.status === 'running'
                      ? '分析中'
                      : nodeMessage?.status === 'completed'
                        ? '已完成'
                        : '等待中'}
                  </Tag>
                </Space>
              </Card>
            )
          })}
        </div>

        {/* Message Stream */}
        <div className="space-y-4">
          {messages.length === 0 && !isConnected && (
            <Card className="text-center py-12">
              <Spin size="large" />
              <div className="mt-4">
                <Text type="secondary">准备开始分析...</Text>
              </div>
            </Card>
          )}

          {messages.map((message, index) => (
            <Card
              key={`${message.node}-${index}`}
              className="overflow-hidden"
              title={
                <div className="flex items-center gap-2">
                  {getNodeIcon(message.node)}
                  <span className="capitalize font-medium">
                    {message.node === 'data_fetcher'
                      ? '数据获取'
                      : message.node === 'fundamental'
                        ? '基本面分析'
                        : message.node === 'technical'
                          ? '技术面分析'
                          : message.node === 'qlib'
                            ? 'Qlib因子分析'
                            : message.node === 'decision'
                              ? '综合决策'
                              : message.node}
                  </span>
                  <Tag color={getNodeStatusColor(message.status)} className="text-xs">
                    {message.status === 'running'
                      ? '分析中'
                      : message.status === 'completed'
                        ? '已完成'
                        : '出错'}
                  </Tag>
                </div>
              }
            >
              {message.content && (
                <div
                  className="prose prose-sm dark:prose-invert max-w-none"
                  dangerouslySetInnerHTML={{ __html: formatContent(message.content) }}
                />
              )}

              {message.data && (
                <div className="mt-4">
                  {message.data.summary && (
                    <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                      <Title level={5}>分析摘要</Title>
                      <Paragraph>{message.data.summary}</Paragraph>
                    </div>
                  )}

                  {message.data.recommendation && (
                    <div className="bg-blue-50 dark:bg-blue-950/20 p-4 rounded-lg mt-3">
                      <Title level={5} className="text-blue-700! dark:text-blue-300!">
                        投资建议
                      </Title>
                      <Paragraph className="text-blue-600! dark:text-blue-400!">
                        {message.data.recommendation}
                      </Paragraph>
                    </div>
                  )}

                  {message.data.score !== undefined && (
                    <div className="mt-3">
                      <Text strong>综合评分：</Text>
                      <Tag
                        color={
                          message.data.score > 0
                            ? 'green'
                            : message.data.score < 0
                              ? 'red'
                              : 'default'
                        }
                      >
                        {message.data.score > 0 ? '看涨' : message.data.score < 0 ? '看跌' : '中性'}
                        ({Math.abs(message.data.score).toFixed(2)})
                      </Tag>
                    </div>
                  )}
                </div>
              )}
            </Card>
          ))}
        </div>

        {/* Loading State */}
        {isConnected && (
          <div className="text-center mt-8">
            <Spin size="large" />
            <Text type="secondary" className="block mt-2">
              正在分析中，请稍候...
            </Text>
          </div>
        )}

        {/* Completion State */}
        {isComplete && (
          <Card className="mt-6 border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950/20 text-center">
            <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-3" />
            <Title level={4} className="text-green-700! dark:text-green-300!">
              分析完成
            </Title>
            <Text type="secondary" className="text-green-600 dark:text-green-400">
              已为您生成完整的股票分析报告
            </Text>
          </Card>
        )}
      </div>
    </div>
  )
}
