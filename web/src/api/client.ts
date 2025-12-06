import axios, { AxiosError } from 'axios'
import type {
  AnalysisReport,
  StockAnalysisRequest,
  StandardResponse,
  StockListResponse,
} from '../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const stockApi = {
  /**
   * 批量分析股票
   */
  analyzeStocks: async (symbols: string[]): Promise<AnalysisReport[]> => {
    const request: StockAnalysisRequest = { symbols }
    try {
      const response = await apiClient.post<StandardResponse<AnalysisReport[]>>(
        '/stock/analyze',
        request
      )
      const result = response.data

      // 检查响应状态码
      if (result.status_code !== 200) {
        throw new Error(result.err_msg || '请求失败')
      }

      // 检查数据是否存在
      if (!result.data) {
        throw new Error(result.err_msg || '未返回数据')
      }

      return result.data
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
}

export default apiClient
