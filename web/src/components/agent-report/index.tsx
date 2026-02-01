import { useParams } from 'react-router-dom'
import { useState, useEffect, useCallback, useRef } from 'react'
import { Spin, Card, Typography, Alert } from 'antd'
import { BarChart3, Brain, FileText } from 'lucide-react'
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
import { StepCard } from './StepCard'

const { Title, Text } = Typography

// 选中步骤枚举
enum AgentStep {
  Fundamental = 'fundamental_analyzer',
  Technical = 'technical_analyzer',
  Coordinator = 'coordinator',
}

// 步骤配置
const STEP_CONFIG: Record<string, { name: string; icon: React.ReactNode; defaultMessage: string }> =
  {
    [AgentStep.Fundamental]: {
      name: '基本面分析',
      icon: <FileText className="h-5 w-5" />,
      defaultMessage: '等待基本面分析...',
    },
    [AgentStep.Technical]: {
      name: '技术面分析',
      icon: <BarChart3 className="h-5 w-5" />,
      defaultMessage: '等待技术面分析...',
    },
    [AgentStep.Coordinator]: {
      name: '综合决策',
      icon: <Brain className="h-5 w-5" />,
      defaultMessage: '等待综合决策...',
    },
  } as const

const STEP_ORDER = [AgentStep.Fundamental, AgentStep.Technical, AgentStep.Coordinator] as const

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
    [AgentStep.Fundamental]: { streaming: '', thinking: '', isStreaming: false, executionTime: 0 },
    [AgentStep.Technical]: { streaming: '', thinking: '', isStreaming: false, executionTime: 0 },
    [AgentStep.Coordinator]: { streaming: '', thinking: '', isStreaming: false, executionTime: 0 },
  })
  const [error, setError] = useState<string | null>(null)
  const [currentSymbol, setCurrentSymbol] = useState<string | null>(null)
  const [hasStarted, setHasStarted] = useState(false)
  const [selectedStep, setAgentStep] = useState<AgentStep>(AgentStep.Fundamental)

  // 获取 step 的根名称（处理 coordinator_streaming 等情况）
  const getStepKey = (step: string): string => {
    if (step.startsWith(AgentStep.Fundamental)) return AgentStep.Fundamental
    if (step.startsWith(AgentStep.Technical)) return AgentStep.Technical
    if (step.startsWith(AgentStep.Coordinator)) return AgentStep.Coordinator
    return step
  }

  const handleMessage = useCallback((event: AgentReportEvent) => {
    switch (event.type) {
      case 'start':
        setCurrentSymbol(event.symbol)
        setHasStarted(true)
        setStepContents({
          [AgentStep.Fundamental]: {
            streaming: '',
            thinking: '',
            isStreaming: false,
            executionTime: 0,
          },
          [AgentStep.Technical]: {
            streaming: '',
            thinking: '',
            isStreaming: false,
            executionTime: 0,
          },
          [AgentStep.Coordinator]: {
            streaming: '',
            thinking: '',
            isStreaming: false,
            executionTime: 0,
          },
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
              executionTime: event.data?.execution_time ?? 0,
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
          const updated: Record<string, StepContent> = { ...prev }
          Object.keys(updated).forEach(key => {
            const current = updated[key]
            updated[key] = {
              streaming: current.streaming,
              thinking: current.thinking,
              isStreaming: false,
              executionTime: current.executionTime,
            }
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
        [AgentStep.Fundamental]: {
          streaming: '',
          thinking: '',
          isStreaming: false,
          executionTime: 0,
        },
        [AgentStep.Technical]: {
          streaming: '',
          thinking: '',
          isStreaming: false,
          executionTime: 0,
        },
        [AgentStep.Coordinator]: {
          streaming: '',
          thinking: '',
          isStreaming: false,
          executionTime: 0,
        },
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
    progressNodes[AgentStep.Fundamental]?.data?.factors || []

  const technical_factors: FactorDetail[] = progressNodes[AgentStep.Technical]?.data?.factors || []

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
              const isSelected = selectedStep === step

              return (
                <StepCard
                  key={step}
                  icon={config.icon}
                  status={status}
                  message={displayMessage}
                  isLoading={isLoading}
                  isSelected={isSelected}
                  onClick={() => setAgentStep(step)}
                />
              )
            })}
          </div>
        )}

        {/* 分析因子 - 根据选中步骤过滤 */}
        {fundamental_factors.length > 0 || technical_factors.length > 0 ? (
          <Card className="mb-8! bg-transparent! animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div>
              {/* 根据 selectedStep 决定显示哪些因子 */}
              {(selectedStep === AgentStep.Fundamental || selectedStep === AgentStep.Coordinator) &&
                fundamental_factors.length > 0 && (
                  <DesktopFactorList
                    title={`基本面 (${fundamental_factors.length})`}
                    factors={fundamental_factors}
                    showAll={true}
                    basic={true}
                  />
                )}
              {selectedStep === AgentStep.Coordinator &&
                fundamental_factors.length > 0 &&
                technical_factors.length > 0 && (
                  <div className="border-t border-gray-100 dark:border-gray-800 my-6" />
                )}
              {(selectedStep === AgentStep.Technical || selectedStep === AgentStep.Coordinator) &&
                technical_factors.length > 0 && (
                  <DesktopFactorList
                    title={`技术面 (${technical_factors.length})`}
                    factors={technical_factors}
                  />
                )}
            </div>
          </Card>
        ) : null}

        {/* 基本面分析 - 思考过程和分析报告 */}
        {selectedStep === AgentStep.Fundamental &&
          (stepContents[AgentStep.Fundamental].thinking ||
            stepContents[AgentStep.Fundamental].streaming) && (
            <div className="mb-6">
              <ThinkingAndReport
                title="基本面分析"
                thinkingContent={stepContents[AgentStep.Fundamental].thinking}
                reportContent={
                  stepContents[AgentStep.Fundamental].streaming ||
                  (analysisResult && progressNodes[AgentStep.Fundamental]?.status === 'completed'
                    ? '分析完成'
                    : '')
                }
                isStreaming={stepContents[AgentStep.Fundamental].isStreaming}
                executionTime={stepContents[AgentStep.Fundamental].executionTime}
              />
            </div>
          )}

        {/* 技术面分析 - 思考过程和分析报告 */}
        {selectedStep === AgentStep.Technical &&
          (stepContents[AgentStep.Technical].thinking ||
            stepContents[AgentStep.Technical].streaming) && (
            <div className="mb-6">
              <ThinkingAndReport
                title="技术面分析"
                thinkingContent={stepContents[AgentStep.Technical].thinking}
                reportContent={
                  stepContents[AgentStep.Technical].streaming ||
                  (analysisResult && progressNodes[AgentStep.Technical]?.status === 'completed'
                    ? '分析完成'
                    : '')
                }
                isStreaming={stepContents[AgentStep.Technical].isStreaming}
                executionTime={stepContents[AgentStep.Technical].executionTime}
              />
            </div>
          )}

        {/* 综合分析 - 思考过程和分析报告 */}
        {selectedStep === AgentStep.Coordinator &&
          (stepContents[AgentStep.Coordinator].thinking ||
            stepContents[AgentStep.Coordinator].streaming ||
            analysisResult?.decision) && (
            <div className="mb-6">
              <ThinkingAndReport
                title="综合分析"
                thinkingContent={stepContents[AgentStep.Coordinator].thinking}
                reportContent={
                  stepContents[AgentStep.Coordinator].streaming ||
                  analysisResult?.decision?.analysis ||
                  ''
                }
                isStreaming={stepContents[AgentStep.Coordinator].isStreaming}
                executionTime={
                  stepContents[AgentStep.Coordinator].executionTime ||
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
