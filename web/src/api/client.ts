import axios, { AxiosError } from 'axios'
import type { AnalysisReport, StandardResponse, StockListResponse } from '../types'

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
  getAgentReport: (symbol: string, onMessage: (data: any) => void) => {
    const eventSource = new EventSource(
      `${API_BASE_URL}/agent/analyze?symbol=${encodeURIComponent(symbol)}`
    )

    eventSource.onmessage = event => {
      try {
        const data = JSON.parse(event.data)
        onMessage(data)
      } catch (error) {
        console.error('解析消息失败:', error)
      }
    }

    eventSource.onerror = error => {
      console.error('SSE连接错误:', error)
      eventSource.close()
    }

    return eventSource
  },
}

export default apiClient
