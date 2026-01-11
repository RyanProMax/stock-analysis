import { Card, Typography } from 'antd'
import { ChevronDown, ChevronRight } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useState } from 'react'

const { Title } = Typography

interface CollapsibleThinkingProps {
  content: string
  autoCollapse?: boolean
}

export function CollapsibleThinking({ content, autoCollapse = false }: CollapsibleThinkingProps) {
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
