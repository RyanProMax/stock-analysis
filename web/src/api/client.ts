import axios from 'axios';
import type { AnalysisReport, StockAnalysisRequest } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const stockApi = {
  /**
   * 批量分析股票
   */
  analyzeStocks: async (symbols: string[]): Promise<AnalysisReport[]> => {
    const request: StockAnalysisRequest = { symbols };
    const response = await apiClient.post<AnalysisReport[]>('/stock/analyze', request);
    return response.data;
  },
};

export default apiClient;

