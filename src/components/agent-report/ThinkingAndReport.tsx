import { Card, Typography, Button } from 'antd'
import { Brain, FileText, Clock, ChevronDown, ChevronUp } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useState, useMemo } from 'react'

const { Title } = Typography

// AI 彩虹标题样式
const aiRainbowTitleClassName =
  'mb-0! bg-linear-to-r from-cyan-600 via-purple-600 to-pink-600 bg-clip-text text-transparent font-medium dark:from-cyan-400 dark:via-purple-400 dark:to-pink-400'

type ViewMode = 'thinking' | 'report'

interface ThinkingAndReportProps {
  thinkingContent?: string
  reportContent?: string
  isStreaming?: boolean
  title?: string
  executionTime?: number // 执行耗时（秒）
  defaultExpanded?: boolean // 默认是否展开
}

// 粗略估算 token 数（中文约 2 字符/token，英文约 4 字符/token）
function estimateTokens(text: string): number {
  if (!text) return 0
  const chineseChars = (text.match(/[\u4e00-\u9fa5]/g) || []).length
  const otherChars = text.length - chineseChars
  return Math.ceil(chineseChars / 2 + otherChars / 4)
}

function formatTime(seconds: number): string {
  if (seconds < 1) return `${Math.round(seconds * 1000)}ms`
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  const mins = Math.floor(seconds / 60)
  const secs = (seconds % 60).toFixed(1)
  return `${mins}m ${secs}s`
}

export function ThinkingAndReport({
  thinkingContent = '',
  reportContent = '',
  isStreaming = false,
  title = 'AI 分析',
  executionTime = 0,
  defaultExpanded = true,
}: ThinkingAndReportProps) {
  const [userSelectedMode, setUserSelectedMode] = useState<ViewMode | null>(null)
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)

  const hasThinking = Boolean(thinkingContent)
  const hasReport = Boolean(reportContent)

  // 计算应该显示的视图模式
  const viewMode = useMemo(() => {
    // 如果用户手动选择了，使用用户选择
    if (userSelectedMode) {
      // 检查用户选择的内容是否可用
      if (userSelectedMode === 'thinking' && !hasThinking) {
        return hasReport ? 'report' : 'thinking'
      }
      if (userSelectedMode === 'report' && !hasReport) {
        return hasThinking ? 'thinking' : 'report'
      }
      return userSelectedMode
    }

    // 自动模式：根据内容状态决定
    // 如果只有思考内容，显示思考
    if (hasThinking && !hasReport) {
      return 'thinking'
    }

    // 如果只有报告内容，显示报告
    if (!hasThinking && hasReport) {
      return 'report'
    }

    // 如果都有内容且不在流式输出中，显示报告
    if (hasThinking && hasReport && !isStreaming) {
      return 'report'
    }

    // 默认显示报告（如果有的话）或思考
    return hasReport ? 'report' : 'thinking'
  }, [userSelectedMode, hasThinking, hasReport, isStreaming])

  const currentContent = viewMode === 'thinking' ? thinkingContent : reportContent
  const thinkingTokens = estimateTokens(thinkingContent)
  const reportTokens = estimateTokens(reportContent)

  // 用户手动切换时记录选择
  const handleSetViewMode = (mode: ViewMode) => {
    setUserSelectedMode(mode)
  }

  // 切换折叠状态
  const toggleExpanded = () => setIsExpanded(!isExpanded)

  // 如果两个都为空，不显示
  if (!hasThinking && !hasReport) {
    return null
  }

  return (
    <div className="ai-rainbow-border relative animate-in fade-in slide-in-from-bottom-4 duration-500">
      <Card
        variant={'borderless'}
        className="bg-white dark:bg-gray-900"
        styles={{
          body: {
            padding: 0,
          },
        }}
        title={
          <div
            className="flex items-center justify-between cursor-pointer"
            onClick={toggleExpanded}
          >
            {/* 左侧：标题 + 折叠图标 */}
            <div className="flex items-center gap-2">
              <Title level={5} className={aiRainbowTitleClassName}>
                {title}
              </Title>
              <div className="flex items-center justify-center w-6 h-6 text-gray-500 dark:text-gray-400">
                {isExpanded ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </div>
            </div>
            {/* 右侧：统计信息 + 切换按钮 - 点击不折叠 */}
            <div className="flex items-center gap-3" onClick={e => e.stopPropagation()}>
              {executionTime > 0 && (
                <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
                  <Clock className="h-3 w-3" />
                  <span>{formatTime(executionTime)}</span>
                </div>
              )}
              {thinkingTokens > 0 && (
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  思考: ~{thinkingTokens}
                </span>
              )}
              {reportTokens > 0 && (
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  报告: ~{reportTokens}
                </span>
              )}
              <div className="flex items-center gap-1">
                {hasThinking && (
                  <Button
                    type="text"
                    size="small"
                    icon={<Brain className="h-4 w-4" />}
                    className={
                      viewMode === 'thinking'
                        ? 'text-(--color-primary)!'
                        : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                    }
                    onClick={() => handleSetViewMode('thinking')}
                  >
                    思考过程
                  </Button>
                )}
                {hasReport && (
                  <Button
                    type="text"
                    size="small"
                    icon={<FileText className="h-4 w-4" />}
                    className={
                      viewMode === 'report'
                        ? 'text-(--color-primary)!'
                        : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                    }
                    onClick={() => handleSetViewMode('report')}
                  >
                    分析报告
                  </Button>
                )}
              </div>
            </div>
          </div>
        }
      >
        {/* 内容区域，带折叠动画 */}
        <div
          className={`overflow-hidden transition-all duration-300 ease-in-out ${
            isExpanded ? 'max-h-[5000px] opacity-100 p-6' : 'max-h-0 opacity-0 pl-6 pr-6'
          }`}
        >
          <div className="prose prose-sm max-w-none dark:prose-invert prose-a:text-cyan-600 dark:prose-a:text-cyan-400 prose-headings:font-bold prose-headings:text-gray-900 dark:prose-headings:text-gray-100 prose-strong:text-gray-900 dark:prose-strong:text-gray-100 prose-code:text-pink-600 dark:prose-code:text-pink-400 prose-pre:bg-gray-900 dark:prose-pre:bg-gray-950">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{currentContent}</ReactMarkdown>
          </div>
          {/* 流式输出时光标 */}
          {isStreaming && (
            <span className="inline-block w-2 h-4 bg-linear-to-r from-cyan-400 via-purple-500 to-pink-500 ml-1 animate-pulse rounded-full align-middle" />
          )}
        </div>
      </Card>
    </div>
  )
}
