import { Progress } from 'antd'

interface ServiceStartupProgressProps {
  progress: number
}

export function ServiceStartupProgress({ progress }: ServiceStartupProgressProps) {
  return (
    <div className="mt-12 flex flex-col items-center gap-4 p-8 h-full justify-center">
      <Progress
        type="circle"
        percent={progress}
        size={60}
        strokeColor={{
          '0%': '#108ee9',
          '100%': '#87d068',
        }}
      />
      <div className="text-gray-500 text-lg">服务启动中...</div>
    </div>
  )
}
