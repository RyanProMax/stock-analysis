import axios, { AxiosError } from 'axios'
import type {
  AnalysisReport,
  StandardResponse,
  StockListResponse,
  AgentReportEvent,
} from '../types'
import { isMockMode, getMockEventSource } from './mock'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080'
const PING_TIMEOUT = 60000

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const stockApi = {
  /**
   * 检查服务是否可用
   */
  ping: async (): Promise<boolean> => {
    try {
      const {
        data: { status_code },
      } = await apiClient.get('/ping')
      return status_code === 200
    } catch (err: any) {
      console.error('Server Not Available', err)
      return false
    }
  },

  /**
   * 启动服务
   */
  waitForService: async (onProgress?: (progress: number) => void): Promise<void> => {
    const PROGRESS_UPDATE_INTERVAL = 500
    const startTime = Date.now()
    let timer: number | null = null

    const updateProgress = () => {
      const elapsed = Date.now() - startTime
      const progress = Math.min(Math.floor((elapsed / PING_TIMEOUT) * 90), 90)
      onProgress?.(progress)
    }

    try {
      updateProgress()
      timer = setInterval(updateProgress, PROGRESS_UPDATE_INTERVAL)
      // await new Promise(resolve => setTimeout(resolve, PING_TIMEOUT))
      const isAlive = await stockApi.ping()
      if (isAlive) {
        onProgress?.(100)
        return
      } else {
        throw new Error('服务启动超时，请稍后重试')
      }
    } finally {
      if (timer) {
        clearInterval(timer)
        timer = null
      }
    }
  },

  /**
   * 批量分析股票
   */
  analyzeStocks: async (symbols: string[]): Promise<AnalysisReport[]> => {
    try {
      const {
        data: { status_code, data, err_msg },
      } = await apiClient.post<StandardResponse<AnalysisReport[]>>('/stock/analyze', { symbols })

      if (status_code !== 200) {
        throw new Error(err_msg || '请求失败')
      }

      if (!data) {
        throw new Error(err_msg || '未返回数据')
      }

      return data
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const axiosError = error as AxiosError<StandardResponse<AnalysisReport[]>>
        if (axiosError.response?.data) {
          const errorData = axiosError.response.data
          throw new Error(errorData.err_msg || '请求失败')
        }
      }
      throw error
    }
  },

  /**
   * 获取股票列表
   */
  getStockList: async (market?: string): Promise<StockListResponse> => {
    try {
      const params = market ? { market } : {}
      const response = await apiClient.get<StandardResponse<StockListResponse>>('/stock/list', {
        params,
      })
      const result = response.data

      if (result.status_code !== 200) {
        throw new Error(result.err_msg || '获取股票列表失败')
      }
      if (!result.data) {
        throw new Error(result.err_msg || '未获取到股票列表数据')
      }
      return result.data
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const axiosError = error as AxiosError<StandardResponse<StockListResponse>>
        if (axiosError.response?.data) {
          const errorData = axiosError.response.data
          throw new Error(errorData.err_msg || '获取股票列表失败')
        }
      }
      throw error
    }
  },

  /**
   * 获取股票解读报告（流式响应）
   */
  getAgentReport: (
    symbol: string,
    onMessage: (data: AgentReportEvent) => void,
    options?: { onError?: (error: string) => void; onComplete?: () => void }
  ) => {
    // Mock 模式：使用模拟数据
    if (isMockMode) {
      console.log('[API] Using mock mode for agent report')
      return getMockEventSource(symbol, onMessage, options)
    }

    // 正常模式：创建真实的 SSE 连接
    const es = new EventSource(`${API_BASE_URL}/agent/analyze?symbol=${encodeURIComponent(symbol)}`)

    // 监听 start 事件
    es.addEventListener('start', (e: Event) => {
      try {
        const data = JSON.parse((e as MessageEvent).data)
        onMessage(data)
      } catch (err) {
        console.error('解析 start 事件失败:', err)
      }
    })

    // 监听 progress 事件
    es.addEventListener('progress', (e: Event) => {
      try {
        const data = JSON.parse((e as MessageEvent).data)
        onMessage(data)
      } catch (err) {
        console.error('解析 progress 事件失败:', err)
      }
    })

    // 监听 thinking 事件 - LLM 流式输出
    es.addEventListener('thinking', (e: Event) => {
      try {
        const data = JSON.parse((e as MessageEvent).data)
        onMessage(data)
      } catch (err) {
        console.error('解析 thinking 事件失败:', err)
      }
    })

    // 监听 streaming 事件 - LLM 流式输出
    es.addEventListener('streaming', (e: Event) => {
      try {
        const data = JSON.parse((e as MessageEvent).data)
        onMessage(data)
      } catch (err) {
        console.error('解析 streaming 事件失败:', err)
      }
    })

    // 监听 error 事件
    es.addEventListener('error', (e: Event) => {
      try {
        const data = JSON.parse((e as MessageEvent).data)
        onMessage(data)
        options?.onError?.(data.message)
      } catch (err) {
        console.error('解析 error 事件失败:', err)
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
        console.error('解析 complete 事件失败:', err)
      }
      es.close()
    })

    es.onerror = error => {
      if (es.readyState !== EventSource.CLOSED) {
        console.error('SSE连接错误', es.readyState, error)
        options?.onError?.('连接服务器失败')
      }
      es.close()
    }

    return es
  },
}

export default apiClient
