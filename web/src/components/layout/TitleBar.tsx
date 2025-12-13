import { Github } from 'lucide-react'
import { TabKey, Tabs } from './constant'

interface TitleBarProps {
  activeTab: TabKey
  onTabChange: (tab: TabKey) => void
}

export function TitleBar({ activeTab, onTabChange }: TitleBarProps) {
  return (
    <header className="pt-8">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-[50px] items-center justify-between">
          {/* 左侧：图标 + 标题 */}
          <button
            onClick={() => onTabChange(TabKey.StockAnalysis)}
            className="cursor-pointer flex items-center gap-3 transition-colors"
          >
            <img
              src={`${import.meta.env.BASE_URL}favicons/android-chrome-192x192.png`}
              alt="Stock Analysis"
              className="h-[50px] w-[50px]"
            />
            <h1
              className="hidden sm:block font-light text-gray-900 transition-colors hover:text-(--color-primary) dark:text-gray-100 dark:hover:text-(--color-primary)"
              style={{ fontSize: '1.5rem' }}
            >
              Stock Analysis
            </h1>
          </button>

          {/* 右侧：文字 tab + icon tab */}
          <div className="flex items-center gap-1">
            {/* 文字 tab */}
            <nav className="flex items-center gap-1">
              {Tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => onTabChange(tab.id)}
                  style={{ fontSize: 'var(--text-s)' }}
                  className={`cursor-pointer px-3 py-1.5 font-medium transition-colors ${
                    activeTab === tab.id
                      ? 'text-(--color-primary)'
                      : 'text-gray-600 hover:text-(--color-primary) dark:text-gray-400 dark:hover:text-(--color-primary)'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>

            {/* icon tab: GitHub 外链 */}
            <a
              href="https://github.com/RyanProMax/stock-analysis"
              target="_blank"
              rel="noopener noreferrer"
              className="cursor-pointer flex items-center rounded-md px-2 py-1.5 text-gray-600 transition-colors hover:text-(--color-primary) dark:text-gray-400 dark:hover:text-(--color-primary)"
              aria-label="GitHub 仓库"
            >
              <Github className="h-5 w-5" />
            </a>
          </div>
        </div>
      </div>
    </header>
  )
}
