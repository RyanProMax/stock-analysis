import { useParams } from 'react-router-dom'
import { useState, useEffect, useCallback, useRef } from 'react'
import { Spin, Card, Typography, Space, Tag, Progress, Alert } from 'antd'
import {
  CheckCircle,
  AlertCircle,
  Clock,
  BarChart3,
  Activity,
  Brain,
  FileText,
  ThumbsUp,
  ThumbsDown,
  Zap,
} from 'lucide-react'
import { stockApi } from '../../api/client'
import type { AgentReportEvent, ProgressNode, AnalysisResult, AnalysisFactor } from '../../types'

const { Title, Text, Paragraph } = Typography

// 步骤名称映射：SSE返回的step -> 显示名称
const STEP_CONFIG: Record<string, { name: string; icon: React.ReactNode; color: string }> = {
  data_fetcher: { name: '数据获取', icon: <Clock className="h-5 w-5" />, color: 'blue' },
  fundamental_analyzer: {
    name: '基本面分析',
    icon: <FileText className="h-5 w-5" />,
    color: 'green',
  },
  financial_report_analyzer: {
    name: '财务报告',
    icon: <FileText className="h-5 w-5" />,
    color: 'emerald',
  },
  technical_analyzer: {
    name: '技术面分析',
    icon: <BarChart3 className="h-5 w-5" />,
    color: 'purple',
  },
  qlib_analyzer: { name: 'Qlib因子', icon: <Activity className="h-5 w-5" />, color: 'orange' },
  decision_maker: { name: '综合决策', icon: <Brain className="h-5 w-5" />, color: 'pink' },
} as const

// 步骤显示顺序
const STEP_ORDER = [
  'data_fetcher',
  'fundamental_analyzer',
  'technical_analyzer',
  'qlib_analyzer',
  'decision_maker',
] as const

// 状态映射：SSE返回的status -> 内部status
const mapStatus = (sseStatus: string): 'running' | 'completed' | 'error' => {
  if (sseStatus === 'success') return 'completed'
  if (sseStatus === 'running') return 'running'
  if (sseStatus === 'error') return 'error'
  return 'running'
}

export function AgentReport() {
  const { symbol } = useParams<{ symbol: string }>()
  // 状态管理
  const [progressNodes, setProgressNodes] = useState<Record<string, ProgressNode>>({})
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isComplete, setIsComplete] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentSymbol, setCurrentSymbol] = useState<string | null>(null)
  const [hasStarted, setHasStarted] = useState(false)

  // 处理 SSE 消息
  const handleMessage = useCallback((event: AgentReportEvent) => {
    switch (event.type) {
      case 'start':
        setCurrentSymbol(event.symbol)
        setIsConnected(true)
        setHasStarted(true)
        break

      case 'progress':
        setProgressNodes(prev => ({
          ...prev,
          [event.step]: {
            step: event.step,
            status: mapStatus(event.status),
            message: event.message,
            data: event.data,
          },
        }))
        break

      case 'error':
        setError(event.message)
        setIsConnected(false)
        break

      case 'complete':
        setAnalysisResult(event.result)
        setIsComplete(true)
        setIsConnected(false)
        // 将所有节点标记为完成
        setProgressNodes(prev => {
          const updated = { ...prev }
          Object.keys(updated).forEach(key => {
            if (updated[key].status === 'running') {
              updated[key] = { ...updated[key], status: 'completed' }
            }
          })
          return updated
        })
        break
    }
  }, [])

  const handleError = useCallback((err: string) => {
    setError(err)
    setIsConnected(false)
  }, [])

  // 使用 ref 追踪当前 symbol，避免重复连接
  const prevSymbolRef = useRef<string | null>(null)

  useEffect(() => {
    if (!symbol) return
    if (symbol === prevSymbolRef.current) return

    // 清理之前的连接
    prevSymbolRef.current = symbol

    // 重置状态 - 批量更新以减少重渲染
    const resetState = () => {
      setProgressNodes({})
      setAnalysisResult(null)
      setIsConnected(true)
      setIsComplete(false)
      setError(null)
      setCurrentSymbol(null)
      setHasStarted(false)
    }

    // 在下一个微任务中重置状态，避免在 effect 中同步调用 setState
    queueMicrotask(resetState)

    // 创建 SSE 连接
    const eventSource = stockApi.getAgentReport(symbol, handleMessage, {
      onError: handleError,
      onComplete: () => {
        setIsComplete(true)
        setIsConnected(false)
      },
    })

    return () => {
      eventSource?.close()
    }
  }, [symbol, handleMessage, handleError])

  // 获取图标颜色类名
  const getIconColorClass = (color: string) => {
    const colorMap: Record<string, string> = {
      blue: 'text-blue-500',
      green: 'text-green-500',
      emerald: 'text-emerald-500',
      purple: 'text-purple-500',
      orange: 'text-orange-500',
      pink: 'text-pink-500',
    }
    return colorMap[color] || 'text-gray-500'
  }

  // 渲染因子卡片
  const renderFactorCard = (name: string, factor: AnalysisFactor) => {
    const isPositive = factor.status === 'bullish'
    const isNegative = factor.status === 'bearish'

    return (
      <Card
        key={name}
        size="small"
        className={`border-l-4 ${
          isPositive
            ? 'border-l-green-500 bg-green-50 dark:bg-green-950/20'
            : isNegative
              ? 'border-l-red-500 bg-red-50 dark:bg-red-950/20'
              : 'border-l-gray-400 bg-gray-50 dark:bg-gray-800/50'
        }`}
      >
        <Space className="flex flex-col w-full" size="small">
          <div className="flex items-center justify-between">
            <Text strong>{name}</Text>
            <Tag color={isPositive ? 'green' : isNegative ? 'red' : 'default'}>{factor.status}</Tag>
          </div>
          {factor.signals && factor.signals.length > 0 && (
            <div className="space-y-1">
              {factor.signals.map((signal, idx) => (
                <div key={idx} className="text-sm text-gray-600 dark:text-gray-400">
                  • {signal}
                </div>
              ))}
            </div>
          )}
          {factor.score !== undefined && (
            <div className="text-sm">
              <Text type="secondary">评分：</Text>
              <Text strong>{factor.score.toFixed(2)}</Text>
            </div>
          )}
        </Space>
      </Card>
    )
  }

  // 计算整体进度
  const calculateProgress = () => {
    const nodes = Object.values(progressNodes)
    if (nodes.length === 0) return 0
    const completed = nodes.filter(n => n.status === 'completed').length
    return Math.floor((completed / 5) * 100)
  }

  return (
    <div className="bg-gray-50 dark:bg-gray-950 transition-colors min-h-screen">
      <div className="container mx-auto px-4 py-6 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-6">
          <Title level={2} className="font-light!">
            {currentSymbol || symbol}
          </Title>
          {isConnected && (
            <div className="flex items-center justify-center gap-2 mt-2">
              <Spin size="small" />
              <Text type="secondary">正在分析中...</Text>
            </div>
          )}
        </div>

        {/* 进度条 */}
        {isConnected && Object.keys(progressNodes).length > 0 && (
          <div className="mb-6">
            <Progress percent={calculateProgress()} status="active" />
          </div>
        )}

        {/* Error State */}
        {error && (
          <Alert
            title={<span className="font-medium">分析失败</span>}
            description={error}
            type="error"
            showIcon
            className="mb-6!"
            closable={{
              onClose: () => setError(null),
            }}
          />
        )}

        {/* 节点进度卡片 - 仅在SSE开始加载后显示 */}
        {hasStarted && (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 mb-6">
            {STEP_ORDER.map(step => {
              const node = progressNodes[step]
              const config = STEP_CONFIG[step]
              const isActive = node?.status === 'running'
              const isCompleted = node?.status === 'completed'
              const hasNode = !!node

              return (
                <Card
                  key={step}
                  size="small"
                  className={`text-center transition-all duration-300 ${
                    isActive
                      ? 'border-blue-400 bg-blue-50 dark:border-blue-600 dark:bg-blue-950/30 shadow-md'
                      : isCompleted
                        ? 'border-green-400 bg-green-50 dark:border-green-600 dark:bg-green-950/20'
                        : hasNode
                          ? 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800/50'
                          : 'border-gray-200 dark:border-gray-700 bg-gray-100 dark:bg-gray-800/30 opacity-60'
                  }`}
                >
                  <Space className="flex flex-col gap-2" size="small">
                    <div className={getIconColorClass(config.color)}>{config.icon}</div>
                    <Text strong className="text-sm">
                      {config.name}
                    </Text>
                    {/* 状态图标 */}
                    {node?.status === 'running' && <Spin size="small" />}
                    {node?.status === 'completed' && (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    )}
                    {node?.status === 'error' && <AlertCircle className="h-4 w-4 text-red-500" />}
                    {node?.message && (
                      <Text className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2">
                        {node.message}
                      </Text>
                    )}
                  </Space>
                </Card>
              )
            })}
          </div>
        )}

        {/* 分析完成后的最终报告 */}
        {isComplete && analysisResult && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* 分析摘要 / 决策分析 */}
            {analysisResult.decision ? (
              <Card title={<Title level={5}>分析报告</Title>}>
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  <Paragraph className="text-base leading-relaxed whitespace-pre-wrap">
                    {analysisResult.decision.analysis}
                  </Paragraph>
                </div>
              </Card>
            ) : analysisResult.summary ? (
              <Card title={<Title level={5}>分析摘要</Title>}>
                <Paragraph className="text-base leading-relaxed">
                  {analysisResult.summary}
                </Paragraph>
              </Card>
            ) : null}

            {/* 关键因素 */}
            {analysisResult.key_factors && (
              <Card title={<Title level={5}>关键因素</Title>}>
                <div className="grid md:grid-cols-2 gap-4">
                  {analysisResult.key_factors.positive?.length > 0 && (
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <ThumbsUp className="h-4 w-4 text-green-500" />
                        <Text strong className="text-green-600 dark:text-green-400">
                          看涨因素
                        </Text>
                      </div>
                      <ul className="space-y-1">
                        {analysisResult.key_factors.positive.map((factor, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                            <Text>{factor}</Text>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {analysisResult.key_factors.negative?.length > 0 && (
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <ThumbsDown className="h-4 w-4 text-red-500" />
                        <Text strong className="text-red-600 dark:text-red-400">
                          看跌因素
                        </Text>
                      </div>
                      <ul className="space-y-1">
                        {analysisResult.key_factors.negative.map((factor, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <AlertCircle className="h-4 w-4 text-red-500 mt-0.5 shrink-0" />
                            <Text>{factor}</Text>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </Card>
            )}

            {/* 技术分析详情 */}
            {analysisResult.technical_analysis &&
              Object.keys(analysisResult.technical_analysis).length > 0 && (
                <Card
                  title={
                    <div className="flex items-center gap-2">
                      <BarChart3 className="h-5 w-5 text-purple-500" />
                      <Title level={5} className="mb-0">
                        技术分析
                      </Title>
                    </div>
                  }
                >
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {Object.entries(analysisResult.technical_analysis).map(([name, factor]) =>
                      renderFactorCard(name, factor)
                    )}
                  </div>
                </Card>
              )}

            {/* 基本面分析详情 */}
            {analysisResult.fundamental_analysis &&
              Object.keys(analysisResult.fundamental_analysis).length > 0 && (
                <Card
                  title={
                    <div className="flex items-center gap-2">
                      <FileText className="h-5 w-5 text-green-500" />
                      <Title level={5} className="mb-0">
                        基本面分析
                      </Title>
                    </div>
                  }
                >
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {Object.entries(analysisResult.fundamental_analysis).map(([name, factor]) =>
                      renderFactorCard(name, factor)
                    )}
                  </div>
                </Card>
              )}

            {/* Qlib 因子分析详情 */}
            {analysisResult.qlib_analysis &&
              Object.keys(analysisResult.qlib_analysis).length > 0 && (
                <Card
                  title={
                    <div className="flex items-center gap-2">
                      <Zap className="h-5 w-5 text-orange-500" />
                      <Title level={5} className="mb-0">
                        量化因子分析
                      </Title>
                    </div>
                  }
                >
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {Object.entries(analysisResult.qlib_analysis).map(([name, factor]) =>
                      renderFactorCard(name, factor)
                    )}
                  </div>
                </Card>
              )}
          </div>
        )}

        {/* 初始加载状态 - 仅在SSE未开始且未完成时显示 */}
        {!hasStarted && !isComplete && !error && (
          <Card className="text-center py-16">
            <Spin size="large" />
            <div className="mt-4">
              <Text type="secondary">正在连接分析服务...</Text>
            </div>
          </Card>
        )}
      </div>
    </div>
  )
}
