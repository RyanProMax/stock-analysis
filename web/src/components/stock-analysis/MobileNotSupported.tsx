import React from 'react'
import { Monitor } from 'lucide-react'

export const MobileNotSupported: React.FC = () => {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 dark:bg-gray-900">
      <div className="text-center">
        <Monitor className="mx-auto mb-4 h-16 w-16 text-gray-400" />
        <h1 className="mb-2 text-xl font-medium text-gray-900 dark:text-gray-100">
          暂不支持移动端
        </h1>
        <p className="text-gray-500 dark:text-gray-400">请使用 PC 端访问以获得更好的体验</p>
      </div>
    </div>
  )
}
