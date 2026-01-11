import type { AgentReportEvent, FactorDetail, AnalysisResult } from '../types'

// Mock 模式开关
export const isMockMode = false

// Mock 延迟时间（毫秒）
const MOCK_DELAYS = {
  start: 500,
  fundamental: 2000,
  technical: 2000,
  streaming: 3000,
  complete: 1000,
}

// Mock 基本面因子数据
const MOCK_FUNDAMENTAL_FACTORS: FactorDetail[] = [
  {
    key: 'pe_ratio',
    name: '市盈率(PE)',
    status: 'neutral',
    bullish_signals: ['PE处于合理区间', '相比行业平均水平偏低'],
    bearish_signals: ['增长速度放缓'],
  },
  {
    key: 'pb_ratio',
    name: '市净率(PB)',
    status: 'bullish',
    bullish_signals: ['PB低于1，具备安全边际', '资产质量良好'],
    bearish_signals: [],
  },
  {
    key: 'roe',
    name: '净资产收益率(ROE)',
    status: 'bullish',
    bullish_signals: ['ROE持续提升', '盈利能力稳定'],
    bearish_signals: [],
  },
  {
    key: 'revenue_growth',
    name: '营收增长率',
    status: 'neutral',
    bullish_signals: ['营收保持正增长'],
    bearish_signals: ['增长率有所下降'],
  },
]

// Mock 技术面因子数据
const MOCK_TECHNICAL_FACTORS: FactorDetail[] = [
  {
    key: 'ma5',
    name: '5日均线',
    status: 'bullish',
    bullish_signals: ['价格位于MA5上方', '短期趋势向上'],
    bearish_signals: [],
  },
  {
    key: 'ma20',
    name: '20日均线',
    status: 'bullish',
    bullish_signals: ['MA20向上发散', '中期趋势良好'],
    bearish_signals: [],
  },
  {
    key: 'rsi',
    name: '相对强弱指数(RSI)',
    status: 'neutral',
    bullish_signals: ['RSI处于中性区域'],
    bearish_signals: ['接近超买区域'],
  },
  {
    key: 'macd',
    name: 'MACD',
    status: 'bullish',
    bullish_signals: ['MACD金叉', '动能转强'],
    bearish_signals: [],
  },
  {
    key: 'volume',
    name: '成交量',
    status: 'bullish',
    bullish_signals: ['放量上涨', '资金流入明显'],
    bearish_signals: [],
  },
]

// Mock 分析结果
const MOCK_ANALYSIS_RESULT: AnalysisResult = {
  symbol: 'MOCK',
  timestamp: new Date().toISOString(),
  decision: {
    action: '买入',
    analysis: `# 综合分析报告

## 投资建议：**买入**

### 核心观点
基于技术面和基本面的综合分析，该股票当前呈现较好的投资价值。

## 技术面分析
- **趋势判断**：短期和中期均线呈多头排列，趋势向上
- **动量指标**：MACD出现金叉信号，RSI处于健康区间
- **成交量**：近期放量上涨，资金流入明显

## 基本面分析
- **估值水平**：PE、PB处于合理区间，具备安全边际
- **盈利能力**：ROE持续提升，盈利质量良好
- **成长性**：营收保持正增长，但增速有所放缓

### 风险提示
1. 短期技术指标接近超买，注意回调风险
2. 营收增长放缓，需关注后续财报表现

*注：本报告为Mock数据，仅供参考`,
  },
}

// Mock 流式输出内容
const MOCK_STREAMING_CONTENT = `# 正在生成AI分析报告...

## 数据处理完成
- 基本面因子：4个
- 技术面因子：5个

## 正在进行综合评估...
分析市场环境...
评估风险收益比...
生成投资建议...
完善报告内容...
`

// 模拟的 EventSource 类
class MockEventSource {
  url: string
  readyState: number = 0
  onerror: ((this: EventSource, ev: Event) => any) | null = null
  private listeners: Map<string, Set<(e: Event) => void>> = new Map()
  private timeoutIds: Set<number> = new Set()
  private closed = false

  constructor(url: string) {
    this.url = url
    this.readyState = 0 // CONNECTING

    // 解析 symbol
    const match = url.match(/symbol=([^&]+)/)
    const symbol = match ? decodeURIComponent(match[1]) : 'UNKNOWN'

    // 模拟连接建立
    const connectTimeout = setTimeout(() => {
      if (this.closed) return
      this.readyState = 1 // OPEN
      this.startMockFlow(symbol)
    }, 100)

    this.timeoutIds.add(connectTimeout as unknown as number)
  }

  private startMockFlow(symbol: string) {
    const events: { event: string; data: AgentReportEvent; delay: number }[] = [
      {
        event: 'start',
        data: { type: 'start', message: '开始分析', symbol },
        delay: MOCK_DELAYS.start,
      },
      {
        event: 'progress',
        data: {
          type: 'progress',
          step: 'fundamental_analyzer',
          status: 'running',
          message: '正在分析基本面数据...',
          timestamp: new Date().toISOString(),
        },
        delay: MOCK_DELAYS.start + 500,
      },
      {
        event: 'progress',
        data: {
          type: 'progress',
          step: 'fundamental_analyzer',
          status: 'success',
          message: '基本面分析完成',
          data: { factors: MOCK_FUNDAMENTAL_FACTORS },
          timestamp: new Date().toISOString(),
        },
        delay: MOCK_DELAYS.start + MOCK_DELAYS.fundamental,
      },
      {
        event: 'progress',
        data: {
          type: 'progress',
          step: 'technical_analyzer',
          status: 'running',
          message: '正在分析技术面数据...',
          timestamp: new Date().toISOString(),
        },
        delay: MOCK_DELAYS.start + MOCK_DELAYS.fundamental + 500,
      },
      {
        event: 'progress',
        data: {
          type: 'progress',
          step: 'technical_analyzer',
          status: 'success',
          message: '技术面分析完成',
          data: { factors: MOCK_TECHNICAL_FACTORS },
          timestamp: new Date().toISOString(),
        },
        delay: MOCK_DELAYS.start + MOCK_DELAYS.fundamental + MOCK_DELAYS.technical,
      },
      {
        event: 'progress',
        data: {
          type: 'progress',
          step: 'coordinator',
          status: 'running',
          message: '正在进行综合决策...',
          timestamp: new Date().toISOString(),
        },
        delay: MOCK_DELAYS.start + MOCK_DELAYS.fundamental + MOCK_DELAYS.technical + 500,
      },
      {
        event: 'streaming',
        data: {
          type: 'streaming',
          step: 'coordinator',
          content: MOCK_STREAMING_CONTENT,
        },
        delay: MOCK_DELAYS.start + MOCK_DELAYS.fundamental + MOCK_DELAYS.technical + 1000,
      },
      {
        event: 'complete',
        data: {
          type: 'complete',
          message: '分析完成',
          result: MOCK_ANALYSIS_RESULT,
        },
        delay:
          MOCK_DELAYS.start +
          MOCK_DELAYS.fundamental +
          MOCK_DELAYS.technical +
          MOCK_DELAYS.streaming +
          MOCK_DELAYS.complete,
      },
    ]

    events.forEach(({ event, data, delay }) => {
      const timeoutId = setTimeout(() => {
        if (this.closed) return
        const listeners = this.listeners.get(event)
        if (listeners) {
          const messageEvent = new MessageEvent(event, { data: JSON.stringify(data) })
          listeners.forEach(listener => listener(messageEvent))
        }
      }, delay)
      this.timeoutIds.add(timeoutId as unknown as number)
    })
  }

  addEventListener(event: string, callback: (e: Event) => void) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event)!.add(callback)
  }

  removeEventListener(event: string, callback: (e: Event) => void) {
    const listeners = this.listeners.get(event)
    if (listeners) {
      listeners.delete(callback)
    }
  }

  close() {
    this.closed = true
    this.readyState = 2 // CLOSED
    this.timeoutIds.forEach(id => clearTimeout(id))
    this.timeoutIds.clear()
    this.listeners.clear()
  }
}

/**
 * 获取 Mock EventSource
 */
export const getMockEventSource = (
  symbol: string,
  onMessage: (data: AgentReportEvent) => void,
  options?: { onError?: (error: string) => void; onComplete?: () => void }
) => {
  const es = new MockEventSource(`/agent/analyze?symbol=${encodeURIComponent(symbol)}`)

  // 监听 start 事件
  es.addEventListener('start', (e: Event) => {
    try {
      const data = JSON.parse((e as MessageEvent).data)
      onMessage(data)
    } catch (err) {
      console.error('[Mock] 解析 start 事件失败:', err)
    }
  })

  // 监听 progress 事件
  es.addEventListener('progress', (e: Event) => {
    try {
      const data = JSON.parse((e as MessageEvent).data)
      onMessage(data)
    } catch (err) {
      console.error('[Mock] 解析 progress 事件失败:', err)
    }
  })

  // 监听 streaming 事件
  es.addEventListener('streaming', (e: Event) => {
    try {
      const data = JSON.parse((e as MessageEvent).data)
      onMessage(data)
    } catch (err) {
      console.error('[Mock] 解析 streaming 事件失败:', err)
    }
  })

  // 监听 error 事件
  es.addEventListener('error', (e: Event) => {
    try {
      const data = JSON.parse((e as MessageEvent).data)
      onMessage(data)
      options?.onError?.(data.message)
    } catch (err) {
      console.error('[Mock] 解析 error 事件失败:', err)
      options?.onError?.('分析过程发生错误')
    }
    es.close()
  })

  // 监听 complete 事件
  es.addEventListener('complete', (e: Event) => {
    try {
      const data = JSON.parse((e as MessageEvent).data)
      onMessage(data)
      options?.onComplete?.()
    } catch (err) {
      console.error('[Mock] 解析 complete 事件失败:', err)
    }
    es.close()
  })

  es.onerror = error => {
    if (es.readyState !== 2) {
      console.error('[Mock] SSE连接错误', es.readyState, error)
      options?.onError?.('连接服务器失败')
    }
    es.close()
  }

  return es
}

export default MockEventSource
