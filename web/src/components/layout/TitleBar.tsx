import { ThemeToggle } from '../theme/ThemeToggle'

type Tab = 'stock-analysis'

interface TitleBarProps {
  activeTab: Tab
  onTabChange: (tab: Tab) => void
}

export function TitleBar({ activeTab, onTabChange }: TitleBarProps) {
  const tabs: Array<{ id: Tab; label: string }> = [{ id: 'stock-analysis', label: '股票分析' }]

  return (
    <header className="sticky top-0 z-50 border-b border-gray-200 bg-white/80 backdrop-blur-sm dark:border-gray-700 dark:bg-gray-900/80">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* 左侧：标题和标签 */}
          <div className="flex items-center gap-6">
            <h1 className="text-xl font-medium text-gray-900 dark:text-gray-100">股票分析</h1>
            <nav className="hidden sm:flex items-center gap-1">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => onTabChange(tab.id)}
                  className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                    activeTab === tab.id
                      ? 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* 右侧：主题切换 */}
          <div className="flex items-center gap-4">
            <ThemeToggle />
          </div>
        </div>
      </div>
    </header>
  )
}
