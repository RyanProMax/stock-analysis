import { useParams } from 'react-router-dom'
import { useState, useEffect, useCallback, useRef } from 'react'
import { Spin, Card, Typography, Alert } from 'antd'
import {
  CheckCircle,
  AlertCircle,
  BarChart3,
  Brain,
  FileText,
  ChevronDown,
  ChevronRight,
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { merge } from 'lodash-es'
import { stockApi } from '../../api/client'
import {
  type AgentReportEvent,
  NodeStatus,
  type ProgressNode,
  type AnalysisResult,
  type FactorDetail,
} from '../../types'
import { FactorList as DesktopFactorList } from '../stock-analysis/desktop/DesktopFactorList'

const { Title, Text } = Typography

// 步骤配置
const STEP_CONFIG: Record<string, { name: string; icon: React.ReactNode; defaultMessage: string }> =
  {
    fundamental_analyzer: {
      name: '基本面分析',
      icon: <FileText className="h-5 w-5" />,
      defaultMessage: '等待基本面分析...',
    },
    technical_analyzer: {
      name: '技术面分析',
      icon: <BarChart3 className="h-5 w-5" />,
      defaultMessage: '等待技术面分析...',
    },
    coordinator: {
      name: '综合决策',
      icon: <Brain className="h-5 w-5" />,
      defaultMessage: '等待综合决策...',
    },
  } as const

const STEP_ORDER = ['fundamental_analyzer', 'technical_analyzer', 'coordinator'] as const

// 节点样式配置
const NODE_STYLES: Record<NodeStatus, string> = {
  [NodeStatus.pending]:
    'border border-gray-200/60 bg-gradient-to-r from-gray-50/50 via-gray-50/30 to-gray-100/50 dark:border-gray-700/50 dark:from-gray-800/30 dark:via-gray-800/20 dark:to-gray-700/30 opacity-70',
  [NodeStatus.fetching]:
    'border border-cyan-400/60 bg-gradient-to-r from-cyan-50 via-blue-50 to-purple-50 dark:from-cyan-950/40 dark:via-blue-950/40 dark:to-purple-950/40 shadow-lg shadow-cyan-500/10',
  [NodeStatus.running]:
    'border border-cyan-400/60 bg-gradient-to-r from-cyan-50 via-blue-50 to-purple-50 dark:from-cyan-950/40 dark:via-blue-950/40 dark:to-purple-950/40 shadow-lg shadow-cyan-500/10',
  [NodeStatus.analyzing]:
    'border border-cyan-400/60 bg-gradient-to-r from-cyan-50 via-blue-50 to-purple-50 dark:from-cyan-950/40 dark:via-blue-950/40 dark:to-purple-950/40 shadow-lg shadow-cyan-500/10',
  [NodeStatus.completed]:
    'border border-emerald-400/60 bg-gradient-to-r from-emerald-50/80 via-green-50/80 to-teal-50/80 dark:from-emerald-950/30 dark:from-green-950/30 dark:to-teal-950/30',
  [NodeStatus.error]:
    'border border-red-400/60 bg-gradient-to-r from-red-50/80 via-orange-50/80 to-yellow-50/80 dark:from-red-950/30 dark:from-orange-950/30 dark:to-yellow-950/30',
}

const NODE_ICON_COLORS: Record<NodeStatus, string> = {
  [NodeStatus.pending]: 'text-gray-400 dark:text-gray-500',
  [NodeStatus.fetching]: 'shimmer-icon',
  [NodeStatus.running]: 'shimmer-icon',
  [NodeStatus.analyzing]: 'shimmer-icon',
  [NodeStatus.completed]: 'text-emerald-500 dark:text-emerald-400',
  [NodeStatus.error]: 'text-red-500 dark:text-red-400',
}

// AI 彩虹标题样式
const aiRainbowTitleClassName =
  'mb-0! bg-gradient-to-r from-cyan-600 via-purple-600 to-pink-600 bg-clip-text text-transparent font-medium dark:from-cyan-400 dark:via-purple-400 dark:to-pink-400'

// AI 彩虹边框卡片组件
const AIRainbowCard = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <div className="ai-rainbow-border relative">
    <Card
      variant={'borderless'}
      className="bg-white dark:bg-gray-900"
      title={
        <Title level={5} className={aiRainbowTitleClassName}>
          {title}
        </Title>
      }
    >
      {children}
    </Card>
  </div>
)

// Markdown 内容渲染组件 - 使用 Tailwind Typography
const MarkdownContent = ({ content, className = '' }: { content: string; className?: string }) => (
  <div
    className={`prose prose-sm max-w-none dark:prose-invert prose-a:text-cyan-600 dark:prose-a:text-cyan-400 prose-headings:font-bold prose-headings:text-gray-900 dark:prose-headings:text-gray-100 prose-strong:text-gray-900 dark:prose-strong:text-gray-100 prose-code:text-pink-600 dark:prose-code:text-pink-400 prose-pre:bg-gray-900 dark:prose-pre:bg-gray-950 ${className}`}
  >
    <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
  </div>
)

// 可折叠的思考过程组件
const CollapsibleThinking = ({
  content,
  autoCollapse = false,
}: {
  content: string
  autoCollapse?: boolean
}) => {
  const [isExpanded, setIsExpanded] = useState(!autoCollapse)

  const toggleExpanded = () => setIsExpanded(prev => !prev)

  return (
    <Card
      variant={'borderless'}
      className="bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 transition-all duration-300"
      title={
        <div
          className="flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity"
          onClick={toggleExpanded}
        >
          {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          <Title level={5} className="text-gray-600 dark:text-gray-400 mb-0!">
            💭 思考过程
          </Title>
        </div>
      }
    >
      <div
        className={`transition-all duration-300 overflow-hidden ${
          isExpanded ? 'max-h-none' : 'max-h-[4.5em] line-clamp-3'
        }`}
      >
        <div
          className={`prose prose-sm max-w-none dark:prose-invert ${isExpanded ? 'opacity-70' : 'opacity-50'}`}
        >
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
        </div>
      </div>
      {/* 流式输出时显示光标 */}
      {isExpanded && (
        <span className="inline-block w-2 h-4 bg-gray-400 ml-1 animate-pulse rounded-full align-middle" />
      )}
    </Card>
  )
}

export function AgentReport() {
  const { symbol } = useParams<{ symbol: string }>()
  const [progressNodes, setProgressNodes] = useState<Record<string, ProgressNode>>({})
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [streamingContent, setStreamingContent] = useState('')
  const [thinkingContent, setThinkingContent] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [currentSymbol, setCurrentSymbol] = useState<string | null>(null)
  const [hasStarted, setHasStarted] = useState(false)
  const [hasStreaming, setHasStreaming] = useState(false)

  const handleMessage = useCallback((event: AgentReportEvent) => {
    switch (event.type) {
      case 'start':
        setCurrentSymbol(event.symbol)
        setHasStarted(true)
        setStreamingContent('')
        setThinkingContent('')
        setHasStreaming(false)
        break

      case 'progress': {
        setProgressNodes(prev =>
          merge({}, prev, {
            [event.step]: event,
          })
        )
        break
      }

      case 'streaming':
        setStreamingContent(prev => prev + event.content)
        setHasStreaming(true)
        setProgressNodes(prev =>
          merge({}, prev, {
            [event.step]: event,
          })
        )
        break

      case 'thinking':
        setThinkingContent(prev => prev + event.content)
        setProgressNodes(prev =>
          merge({}, prev, {
            [event.step]: event,
          })
        )
        break

      case 'error':
        setError(event.message)
        break

      case 'complete':
        setAnalysisResult(event.result)
        setStreamingContent('')
        setHasStreaming(false)
        // 将所有运行中的节点标记为完成
        setProgressNodes(prev =>
          Object.fromEntries(
            Object.entries(prev).map(([k, v]) => [
              k,
              v.status === NodeStatus.running ? { ...v, status: NodeStatus.completed } : v,
            ])
          )
        )
        break
    }
  }, [])

  const handleError = useCallback((err: string) => {
    setError(err)
  }, [])

  const prevSymbolRef = useRef<string | null>(null)

  useEffect(() => {
    if (!symbol || symbol === prevSymbolRef.current) return

    prevSymbolRef.current = symbol

    // 重置状态
    queueMicrotask(() => {
      setProgressNodes({})
      setAnalysisResult(null)
      setStreamingContent('')
      setThinkingContent('')
      setError(null)
      setCurrentSymbol(null)
      setHasStarted(false)
      setHasStreaming(false)
    })

    const eventSource = stockApi.getAgentReport(symbol, handleMessage, {
      onError: handleError,
    })

    return () => {
      eventSource?.close()
    }
  }, [symbol, handleMessage, handleError])

  const fundamental_factors: FactorDetail[] =
    progressNodes['fundamental_analyzer']?.data?.factors || []

  const technical_factors: FactorDetail[] = progressNodes['technical_analyzer']?.data?.factors || []

  console.log('progressNode', progressNodes)

  return (
    <div className="bg-gray-50 dark:bg-gray-950 transition-colors min-h-screen">
      <div className="container mx-auto px-4 py-6 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-6">
          <Title level={2} className="font-light!">
            {currentSymbol || symbol}
          </Title>
        </div>

        {/* 错误提示 */}
        {error && (
          <Alert
            title={<span className="font-medium">分析失败</span>}
            description={error}
            type="error"
            showIcon
            className="mb-6!"
            closable={{ onClose: () => setError(null) }}
          />
        )}

        {/* 节点进度卡片 */}
        {hasStarted && (
          <div className="grid grid-cols-3 gap-3 mb-6">
            {STEP_ORDER.map(step => {
              const node = progressNodes[step]
              const config = STEP_CONFIG[step]
              const status: NodeStatus = node?.status || NodeStatus.pending
              const displayMessage = node?.message || config.defaultMessage
              const isLoading = [
                NodeStatus.fetching,
                NodeStatus.running,
                NodeStatus.analyzing,
              ].includes(status)

              return (
                <Card
                  key={step}
                  size="small"
                  className={`text-center transition-all duration-500 ${NODE_STYLES[status]}`}
                >
                  <div className="flex flex-col items-center gap-2">
                    <div className={NODE_ICON_COLORS[status]}>{config.icon}</div>
                    <div className={`flex items-center gap-1.5 ${isLoading ? 'shimmer-icon' : ''}`}>
                      {status === NodeStatus.running && <Spin size="small" />}
                      {status === NodeStatus.completed && (
                        <CheckCircle className="h-4 w-4 shrink-0" />
                      )}
                      {status === NodeStatus.error && <AlertCircle className="h-4 w-4 shrink-0" />}
                      <Text className="text-xs text-gray-600 dark:text-gray-400 truncate">
                        {displayMessage}
                      </Text>
                    </div>
                  </div>
                </Card>
              )
            })}
          </div>
        )}

        {/* 分析因子 - 合并基本面和技术面 */}
        {fundamental_factors.length > 0 || technical_factors.length > 0 ? (
          <Card className="mb-8! animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div>
              {fundamental_factors.length > 0 && (
                <DesktopFactorList
                  title={`基本面 (${fundamental_factors.length})`}
                  factors={fundamental_factors}
                  showAll={true}
                />
              )}
              {fundamental_factors.length > 0 && technical_factors.length > 0 && (
                <div className="border-t border-gray-100 dark:border-gray-800 my-6" />
              )}
              {technical_factors.length > 0 && (
                <DesktopFactorList
                  title={`技术面 (${technical_factors.length})`}
                  factors={technical_factors}
                />
              )}
            </div>
          </Card>
        ) : null}

        {/* LLM 思考过程 - 可折叠，有流式输出时自动折叠 */}
        {thinkingContent && (
          <div className="mb-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <CollapsibleThinking
              key={hasStreaming ? 'collapsed' : 'expanded'}
              content={thinkingContent}
              autoCollapse={hasStreaming}
            />
          </div>
        )}

        {/* 分析完成报告 - 使用 AI 彩虹边框 */}
        {analysisResult?.decision || streamingContent ? (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <AIRainbowCard title={!analysisResult?.decision ? 'AI 分析中' : 'AI 分析报告'}>
              <MarkdownContent content={analysisResult?.decision?.analysis || streamingContent} />
              {!analysisResult?.decision && (
                <span className="inline-block w-2 h-4 bg-linear-to-r from-cyan-400 via-purple-500 to-pink-500 ml-1 animate-pulse rounded-full align-middle" />
              )}
            </AIRainbowCard>
          </div>
        ) : null}

        {/* 初始加载状态 */}
        {!hasStarted && !analysisResult && !error && (
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
