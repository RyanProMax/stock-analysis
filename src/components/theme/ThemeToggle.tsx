import { Moon, Sun, Monitor } from 'lucide-react'
import { useTheme } from '../../hooks/useTheme'

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  const themes: Array<{
    value: 'light' | 'dark' | 'system'
    icon: React.ReactNode
    label: string
  }> = [
    { value: 'light', icon: <Sun className="h-4 w-4" />, label: '亮色' },
    { value: 'dark', icon: <Moon className="h-4 w-4" />, label: '暗黑' },
    { value: 'system', icon: <Monitor className="h-4 w-4" />, label: '跟随系统' },
  ]

  return (
    <div className="flex items-center gap-1 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-1">
      {themes.map(t => (
        <button
          key={t.value}
          onClick={() => setTheme(t.value)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium transition-colors ${
            theme === t.value
              ? 'bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900'
              : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
          }`}
          title={t.label}
        >
          {t.icon}
          <span className="hidden sm:inline">{t.label}</span>
        </button>
      ))}
    </div>
  )
}
