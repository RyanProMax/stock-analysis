import { useParams } from 'react-router-dom'
import { useState, useEffect, useCallback, useRef } from 'react'
import { Spin, Card, Typography, Alert } from 'antd'
import { CheckCircle, AlertCircle, BarChart3, Brain, FileText } from 'lucide-react'
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
import { ThinkingAndReport } from './ThinkingAndReport'

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

// 每个 step 的流式内容状态
interface StepContent {
  streaming: string
  thinking: string
  isStreaming: boolean
  executionTime: number // 执行耗时（秒）
}

export function AgentReport() {
  const { symbol } = useParams<{ symbol: string }>()
  const [progressNodes, setProgressNodes] = useState<Record<string, ProgressNode>>({})
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [stepContents, setStepContents] = useState<Record<string, StepContent>>({
    fundamental_analyzer: { streaming: '', thinking: '', isStreaming: false, executionTime: 0 },
    technical_analyzer: { streaming: '', thinking: '', isStreaming: false, executionTime: 0 },
    coordinator: { streaming: '', thinking: '', isStreaming: false, executionTime: 0 },
  })
  const [error, setError] = useState<string | null>(null)
  const [currentSymbol, setCurrentSymbol] = useState<string | null>(null)
  const [hasStarted, setHasStarted] = useState(false)

  // 获取 step 的根名称（处理 coordinator_streaming 等情况）
  const getStepKey = (step: string): string => {
    if (step.startsWith('fundamental_analyzer')) return 'fundamental_analyzer'
    if (step.startsWith('technical_analyzer')) return 'technical_analyzer'
    if (step.startsWith('coordinator')) return 'coordinator'
    return step
  }

  const handleMessage = useCallback((event: AgentReportEvent) => {
    switch (event.type) {
      case 'start':
        setCurrentSymbol(event.symbol)
        setHasStarted(true)
        setStepContents({
          fundamental_analyzer: {
            streaming: '',
            thinking: '',
            isStreaming: false,
            executionTime: 0,
          },
          technical_analyzer: { streaming: '', thinking: '', isStreaming: false, executionTime: 0 },
          coordinator: { streaming: '', thinking: '', isStreaming: false, executionTime: 0 },
        })
        break

      case 'progress': {
        setProgressNodes(prev =>
          merge({}, prev, {
            [event.step]: event,
          })
        )
        // 提取执行时间
        if (event.data?.execution_time) {
          const stepKey = getStepKey(event.step)
          setStepContents(prev => ({
            ...prev,
            [stepKey]: {
              ...prev[stepKey],
              executionTime: event.data!.execution_time,
            },
          }))
        }
        break
      }

      case 'streaming': {
        const stepKey = getStepKey(event.step)
        setStepContents(prev => ({
          ...prev,
          [stepKey]: {
            ...prev[stepKey],
            streaming: prev[stepKey].streaming + event.content,
            isStreaming: true,
          },
        }))
        setProgressNodes(prev =>
          merge({}, prev, {
            [event.step]: event,
          })
        )
        break
      }

      case 'thinking': {
        const stepKey = getStepKey(event.step)
        setStepContents(prev => ({
          ...prev,
          [stepKey]: {
            ...prev[stepKey],
            thinking: prev[stepKey].thinking + event.content,
          },
        }))
        setProgressNodes(prev =>
          merge({}, prev, {
            [event.step]: event,
          })
        )
        break
      }

      case 'error':
        setError(event.message)
        break

      case 'complete':
        setAnalysisResult(event.result)
        // 停止所有流式状态
        setStepContents(prev => {
          const updated = { ...prev }
          Object.keys(updated).forEach(key => {
            updated[key] = { ...updated[key], isStreaming: false }
          })
          return updated
        })
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
      setStepContents({
        fundamental_analyzer: { streaming: '', thinking: '', isStreaming: false, executionTime: 0 },
        technical_analyzer: { streaming: '', thinking: '', isStreaming: false, executionTime: 0 },
        coordinator: { streaming: '', thinking: '', isStreaming: false, executionTime: 0 },
      })
      setError(null)
      setCurrentSymbol(null)
      setHasStarted(false)
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

        {/* 基本面分析 - 思考过程和分析报告 */}
        {(stepContents.fundamental_analyzer.thinking ||
          stepContents.fundamental_analyzer.streaming) && (
          <div className="mb-6">
            <ThinkingAndReport
              title="基本面分析"
              thinkingContent={stepContents.fundamental_analyzer.thinking}
              reportContent={
                stepContents.fundamental_analyzer.streaming ||
                (analysisResult && progressNodes.fundamental_analyzer?.status === 'completed'
                  ? '分析完成'
                  : '')
              }
              isStreaming={stepContents.fundamental_analyzer.isStreaming}
              executionTime={stepContents.fundamental_analyzer.executionTime}
            />
          </div>
        )}

        {/* 技术面分析 - 思考过程和分析报告 */}
        {(stepContents.technical_analyzer.thinking ||
          stepContents.technical_analyzer.streaming) && (
          <div className="mb-6">
            <ThinkingAndReport
              title="技术面分析"
              thinkingContent={stepContents.technical_analyzer.thinking}
              reportContent={
                stepContents.technical_analyzer.streaming ||
                (analysisResult && progressNodes.technical_analyzer?.status === 'completed'
                  ? '分析完成'
                  : '')
              }
              isStreaming={stepContents.technical_analyzer.isStreaming}
              executionTime={stepContents.technical_analyzer.executionTime}
            />
          </div>
        )}

        {/* 综合分析 - 思考过程和分析报告 */}
        {(stepContents.coordinator.thinking ||
          stepContents.coordinator.streaming ||
          analysisResult?.decision) && (
          <div className="mb-6">
            <ThinkingAndReport
              title="综合分析"
              thinkingContent={stepContents.coordinator.thinking}
              reportContent={
                stepContents.coordinator.streaming || analysisResult?.decision?.analysis || ''
              }
              isStreaming={stepContents.coordinator.isStreaming}
              executionTime={
                stepContents.coordinator.executionTime ||
                analysisResult?.execution_times?.CoordinatorAgent ||
                0
              }
            />
          </div>
        )}

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
