import React from 'react'
import { TrendingUp, TrendingDown, Activity, BarChart3 } from 'lucide-react'
import type {
  TrendAnalysisResult,
  TrendStatus,
  BuySignal,
  MACDStatus,
  RSIStatus,
  VolumeStatus,
} from '../../../types'

interface TrendAnalysisTabProps {
  trend: TrendAnalysisResult
}

// 获取趋势状态样式 - 参考因子卡片
const getTrendStatusStyle = (
  status: TrendStatus
): { bg: string; border: string; dot: string; text: string } => {
  if (status === '强势多头' || status === '多头排列') {
    return {
      bg: 'bg-emerald-50/50 dark:bg-emerald-900/20',
      border: 'border-emerald-200 dark:border-emerald-800',
      dot: 'bg-emerald-500',
      text: 'text-emerald-700 dark:text-emerald-300',
    }
  }
  if (status === '强势空头' || status === '空头排列') {
    return {
      bg: 'bg-rose-50/50 dark:bg-rose-900/20',
      border: 'border-rose-200 dark:border-rose-800',
      dot: 'bg-rose-500',
      text: 'text-rose-700 dark:text-rose-300',
    }
  }
  return {
    bg: 'bg-amber-50/50 dark:bg-amber-900/20',
    border: 'border-amber-200 dark:border-amber-800',
    dot: 'bg-amber-500',
    text: 'text-amber-700 dark:text-amber-300',
  }
}

// 获取买入信号样式
const getBuySignalStyle = (signal: BuySignal): { bg: string; text: string } => {
  if (signal === '强烈买入' || signal === '买入') {
    return {
      bg: 'bg-emerald-100 dark:bg-emerald-900/30',
      text: 'text-emerald-800 dark:text-emerald-200',
    }
  }
  if (signal === '强烈卖出' || signal === '卖出') {
    return {
      bg: 'bg-rose-100 dark:bg-rose-900/30',
      text: 'text-rose-800 dark:text-rose-200',
    }
  }
  return {
    bg: 'bg-gray-100 dark:bg-gray-800',
    text: 'text-gray-700 dark:text-gray-300',
  }
}

// MACD 状态样式
const getMACDStatusStyle = (status: MACDStatus): string => {
  if (status.includes('金叉') || status === '多头' || status === '上穿零轴') {
    return 'text-emerald-600 dark:text-emerald-400'
  }
  if (status.includes('死叉') || status === '空头' || status === '下穿零轴') {
    return 'text-rose-600 dark:text-rose-400'
  }
  return 'text-gray-600 dark:text-gray-400'
}

// RSI 状态样式
const getRSIStatusStyle = (status: RSIStatus): string => {
  if (status === '超买') {
    return 'text-rose-600 dark:text-rose-400'
  }
  if (status === '超卖') {
    return 'text-emerald-600 dark:text-emerald-400'
  }
  if (status === '强势买入') {
    return 'text-emerald-600 dark:text-emerald-400'
  }
  return 'text-gray-600 dark:text-gray-400'
}

// 量能状态样式
const getVolumeStatusStyle = (status: VolumeStatus): string => {
  if (status === '放量上涨') {
    return 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20'
  }
  if (status === '放量下跌') {
    return 'text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-900/20'
  }
  return 'text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800'
}

export const TrendAnalysisTab: React.FC<TrendAnalysisTabProps> = ({ trend }) => {
  const trendStyle = getTrendStatusStyle(trend.trend_status)
  const signalStyle = getBuySignalStyle(trend.buy_signal)

  return (
    <div className="space-y-4">
      {/* 核心信号 + 均线分析 - 两列布局 */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* 核心信号卡片 - 参考多因子分析样式 */}
        <div
          className={`overflow-hidden rounded-lg border transition-all ${trendStyle.border} ${trendStyle.bg} shadow-sm hover:shadow-md`}
        >
          <div className="p-4">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className={`h-2 w-2 rounded-full ${trendStyle.dot}`} />
                <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">核心信号</h4>
              </div>
              {/* 买入信号标签 */}
              <div className={`rounded-md px-2 py-0.5 ${signalStyle.bg}`}>
                <span className={`text-xs font-semibold ${signalStyle.text}`}>
                  {trend.buy_signal}
                </span>
              </div>
            </div>

            <div className="mb-3 flex items-center justify-between">
              <span className="text-xs text-gray-500 dark:text-gray-400">{trend.trend_status}</span>
              <span className={`text-xs font-medium ${trendStyle.text}`}>
                强度: {trend.trend_strength.toFixed(0)}
              </span>
            </div>

            <div className="h-1.5 mb-3 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
              <div
                className="h-full rounded-full bg-emerald-500"
                style={{ width: `${trend.trend_strength}%` }}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="mb-1 text-xs text-gray-500 dark:text-gray-400">当前价格</p>
                <p className="text-sm font-bold text-gray-900 dark:text-gray-100">
                  ${trend.current_price.toFixed(2)}
                </p>
              </div>
            </div>

            {/* 信号理由 */}
            {trend.signal_reasons.length > 0 && (
              <div className="mt-3 space-y-1.5">
                {trend.signal_reasons.slice(0, 2).map((reason, idx) => (
                  <div key={idx} className="flex items-start gap-1.5">
                    <TrendingUp className="h-3 w-3 shrink-0 text-emerald-600 dark:text-emerald-400 mt-0.5" />
                    <span className="text-xs leading-relaxed text-gray-700 dark:text-gray-300">
                      {reason}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* 风险因素 */}
            {trend.risk_factors.length > 0 && (
              <div className="mt-2 space-y-1.5">
                {trend.risk_factors.slice(0, 2).map((risk, idx) => (
                  <div key={idx} className="flex items-start gap-1.5">
                    <TrendingDown className="h-3 w-3 shrink-0 text-rose-600 dark:text-rose-400 mt-0.5" />
                    <span className="text-xs leading-relaxed text-gray-700 dark:text-gray-300">
                      {risk}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 均线分析卡片 - 参考多因子分析样式 */}
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-gray-50/80 dark:border-gray-700 dark:bg-gray-800/60 shadow-sm hover:shadow-md">
          <div className="p-4">
            <div className="mb-3 flex items-center gap-2">
              <Activity className="h-4 w-4 text-gray-500" />
              <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">均线分析</h4>
            </div>

            <div className="mb-3">
              <p className="mb-1 text-xs text-gray-500 dark:text-gray-400">均线排列</p>
              <p className="text-xs text-gray-900 dark:text-gray-100">{trend.ma_alignment}</p>
            </div>

            <div className="mb-3 grid grid-cols-4 gap-2">
              <div>
                <p className="mb-0.5 text-xs text-gray-500 dark:text-gray-400">MA5</p>
                <p className="text-xs font-semibold text-gray-900 dark:text-gray-100">
                  {trend.ma5.toFixed(1)}
                </p>
              </div>
              <div>
                <p className="mb-0.5 text-xs text-gray-500 dark:text-gray-400">MA10</p>
                <p className="text-xs font-semibold text-gray-900 dark:text-gray-100">
                  {trend.ma10.toFixed(1)}
                </p>
              </div>
              <div>
                <p className="mb-0.5 text-xs text-gray-500 dark:text-gray-400">MA20</p>
                <p className="text-xs font-semibold text-gray-900 dark:text-gray-100">
                  {trend.ma20.toFixed(1)}
                </p>
              </div>
              <div>
                <p className="mb-0.5 text-xs text-gray-500 dark:text-gray-400">MA60</p>
                <p className="text-xs font-semibold text-gray-900 dark:text-gray-100">
                  {trend.ma60.toFixed(1)}
                </p>
              </div>
            </div>

            {/* 支撑压力 */}
            <div className="grid grid-cols-2 gap-2">
              <div>
                <p className="mb-1 text-xs text-gray-500 dark:text-gray-400">支撑</p>
                <div className="flex flex-wrap gap-1">
                  {trend.support_levels.slice(0, 3).map((level, idx) => (
                    <span
                      key={idx}
                      className="rounded border border-emerald-300 bg-emerald-50 px-1.5 py-0.5 text-xs font-medium text-emerald-700 dark:border-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300"
                    >
                      {level.toFixed(1)}
                    </span>
                  ))}
                  {trend.support_levels.length === 0 && (
                    <span className="text-xs text-gray-400 dark:text-gray-500">-</span>
                  )}
                </div>
              </div>
              <div>
                <p className="mb-1 text-xs text-gray-500 dark:text-gray-400">压力</p>
                <div className="flex flex-wrap gap-1">
                  {trend.resistance_levels.slice(0, 3).map((level, idx) => (
                    <span
                      key={idx}
                      className="rounded border border-rose-300 bg-rose-50 px-1.5 py-0.5 text-xs font-medium text-rose-700 dark:border-rose-700 dark:bg-rose-900/30 dark:text-rose-300"
                    >
                      {level.toFixed(1)}
                    </span>
                  ))}
                  {trend.resistance_levels.length === 0 && (
                    <span className="text-xs text-gray-400 dark:text-gray-500">-</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 技术指标 - 参考多因子分析样式 */}
      <div className="overflow-hidden rounded-lg border border-gray-200 bg-gray-50/80 dark:border-gray-700 dark:bg-gray-800/60 shadow-sm hover:shadow-md">
        <div className="p-4">
          <div className="mb-3 flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-gray-500" />
            <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">技术指标</h4>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            {/* MACD */}
            <div className="rounded-lg bg-gray-50/80 p-3 dark:bg-gray-900/30 border border-gray-200 dark:border-gray-700">
              <div className="mb-2 flex items-center justify-between">
                <p className="text-xs font-medium text-gray-700 dark:text-gray-300">MACD</p>
                <p
                  className={`rounded-md px-2 py-0.5 text-xs font-medium ${getMACDStatusStyle(trend.macd_status)}`}
                >
                  {trend.macd_status}
                </p>
              </div>
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500 dark:text-gray-400">DIF</span>
                  <span className="text-xs font-semibold text-gray-900 dark:text-gray-100">
                    {trend.macd_dif.toFixed(3)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500 dark:text-gray-400">DEA</span>
                  <span className="text-xs font-semibold text-gray-900 dark:text-gray-100">
                    {trend.macd_dea.toFixed(3)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500 dark:text-gray-400">BAR</span>
                  <span
                    className={`text-xs font-semibold ${
                      trend.macd_bar >= 0
                        ? 'text-emerald-600 dark:text-emerald-400'
                        : 'text-rose-600 dark:text-rose-400'
                    }`}
                  >
                    {trend.macd_bar >= 0 ? '+' : ''}
                    {trend.macd_bar.toFixed(3)}
                  </span>
                </div>
              </div>
            </div>

            {/* RSI */}
            <div className="rounded-lg bg-gray-50/80 p-3 dark:bg-gray-900/30 border border-gray-200 dark:border-gray-700">
              <div className="mb-2 flex items-center justify-between">
                <p className="text-xs font-medium text-gray-700 dark:text-gray-300">RSI</p>
                <p
                  className={`rounded-md px-2 py-0.5 text-xs font-medium ${getRSIStatusStyle(trend.rsi_status)}`}
                >
                  {trend.rsi_status}
                </p>
              </div>
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500 dark:text-gray-400">RSI(6)</span>
                  <span className="text-xs font-semibold text-gray-900 dark:text-gray-100">
                    {trend.rsi_6.toFixed(1)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500 dark:text-gray-400">RSI(12)</span>
                  <span className="text-xs font-semibold text-gray-900 dark:text-gray-100">
                    {trend.rsi_12.toFixed(1)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500 dark:text-gray-400">RSI(24)</span>
                  <span className="text-xs font-semibold text-gray-900 dark:text-gray-100">
                    {trend.rsi_24.toFixed(1)}
                  </span>
                </div>
              </div>
            </div>

            {/* 量能分析 */}
            <div className="rounded-lg bg-gray-50/80 p-3 dark:bg-gray-900/30 border border-gray-200 dark:border-gray-700">
              <div className="mb-2 flex items-center justify-between">
                <p className="text-xs font-medium text-gray-700 dark:text-gray-300">量能</p>
                <p
                  className={`rounded-md px-2 py-0.5 text-xs font-medium ${getVolumeStatusStyle(trend.volume_status)}`}
                >
                  {trend.volume_status}
                </p>
              </div>
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500 dark:text-gray-400">量比(5日)</span>
                  <span className="text-xs font-semibold text-gray-900 dark:text-gray-100">
                    {trend.volume_ratio_5d.toFixed(2)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500 dark:text-gray-400">量能趋势</span>
                  <span className="text-xs font-semibold text-gray-900 dark:text-gray-100">
                    {trend.volume_trend || '-'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
