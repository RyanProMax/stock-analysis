import { Card, Typography } from 'antd'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const { Title } = Typography

// AI 彩虹标题样式
export const aiRainbowTitleClassName =
  'mb-0! bg-gradient-to-r from-cyan-600 via-purple-600 to-pink-600 bg-clip-text text-transparent font-medium dark:from-cyan-400 dark:via-purple-400 dark:to-pink-400'

// AI 彩虹边框卡片组件
export function AIRainbowCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
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
}

// Markdown 内容渲染组件 - 使用 Tailwind Typography
export function MarkdownContent({
  content,
  className = '',
}: {
  content: string
  className?: string
}) {
  return (
    <div
      className={`prose prose-sm max-w-none dark:prose-invert prose-a:text-cyan-600 dark:prose-a:text-cyan-400 prose-headings:font-bold prose-headings:text-gray-900 dark:prose-headings:text-gray-100 prose-strong:text-gray-900 dark:prose-strong:text-gray-100 prose-code:text-pink-600 dark:prose-code:text-pink-400 prose-pre:bg-gray-900 dark:prose-pre:bg-gray-950 ${className}`}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  )
}
