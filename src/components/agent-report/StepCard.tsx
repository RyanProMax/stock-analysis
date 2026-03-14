import { CheckCircle, AlertCircle } from 'lucide-react'

interface StepCardProps {
  icon: React.ReactNode
  status: string
  message: string
  isLoading: boolean
  isSelected: boolean
  onClick: () => void
}

const NODE_ICON_COLORS: Record<string, string> = {
  pending: 'text-gray-400 dark:text-gray-500',
  fetching: 'shimmer-icon',
  running: 'shimmer-icon',
  analyzing: 'shimmer-icon',
  completed: 'text-emerald-500 dark:text-emerald-400',
  error: 'text-red-500 dark:text-red-400',
}

const SPINNER_SVG = (
  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
    <circle
      className="opacity-25"
      cx="12"
      cy="12"
      r="10"
      stroke="currentColor"
      strokeWidth="4"
      fill="none"
    />
    <path
      className="opacity-75"
      fill="currentColor"
      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
    />
  </svg>
)

export function StepCard({ icon, status, message, isLoading, isSelected, onClick }: StepCardProps) {
  return (
    <div
      className={`relative rounded-lg cursor-pointer select-none transition-all duration-300 focus:outline-none ${
        isSelected
          ? 'p-[1.5px] bg-linear-to-r from-cyan-400 via-purple-400 to-pink-400 bg-size-[200%_100%] animate-gradient-flow'
          : 'p-[1.5px] bg-gray-50/50 dark:bg-gray-800/30 hover:bg-linear-to-r hover:from-cyan-50/80 hover:via-purple-50/80 hover:to-pink-50/80 dark:hover:from-cyan-950/50 dark:hover:via-purple-950/50 dark:hover:to-pink-950/50'
      }`}
      onClick={onClick}
    >
      <div
        className={`bg-white dark:bg-gray-900 rounded-md flex flex-col items-center gap-2 py-3 px-4 border ${
          isSelected ? 'border-transparent' : 'border-gray-200/60 dark:border-gray-700/50'
        }`}
      >
        <div className={NODE_ICON_COLORS[status]}>{icon}</div>
        <div className={`flex items-center gap-1.5 ${isLoading ? 'shimmer-icon' : ''}`}>
          {status === 'running' && SPINNER_SVG}
          {status === 'completed' && (
            <CheckCircle className="h-4 w-4 shrink-0 text-emerald-500 dark:text-emerald-400" />
          )}
          {status === 'error' && <AlertCircle className="h-4 w-4 shrink-0" />}
          <span
            className={`text-xs truncate ${
              status === 'completed'
                ? 'text-emerald-500 dark:text-emerald-400'
                : 'text-gray-600 dark:text-gray-400'
            }`}
          >
            {message}
          </span>
        </div>
      </div>
    </div>
  )
}
