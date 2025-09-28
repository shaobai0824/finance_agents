import axios, { AxiosResponse } from 'axios';
import {
  ApiError,
  HealthCheckResponse,
  QueryRequest,
  QueryResponse,
  SessionInfo,
  SystemStats
} from '../types';

// API 基礎設定
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30秒超時
  headers: {
    'Content-Type': 'application/json',
  },
});

// 請求攔截器（添加 loading 狀態）
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// 回應攔截器（統一錯誤處理）
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error);

    // 統一錯誤格式
    const apiError: ApiError = {
      error_code: error.response?.data?.error_code || 'UNKNOWN_ERROR',
      error_message: error.response?.data?.error_message || error.message || '未知錯誤',
      details: error.response?.data?.details || { status: error.response?.status }
    };

    return Promise.reject(apiError);
  }
);

// API 服務類別
export class FinanceAgentsAPI {

  /**
   * 健康檢查
   */
  static async healthCheck(): Promise<HealthCheckResponse> {
    const response: AxiosResponse<HealthCheckResponse> = await apiClient.get('/health');
    return response.data;
  }

  /**
   * 發送理財諮詢查詢
   */
  static async sendQuery(request: QueryRequest): Promise<QueryResponse> {
    const response: AxiosResponse<QueryResponse> = await apiClient.post('/query', request);
    return response.data;
  }

  /**
   * 取得會話狀態
   */
  static async getSessionStatus(sessionId: string): Promise<any> {
    const response = await apiClient.get(`/session/${sessionId}/status`);
    return response.data;
  }

  /**
   * 取得會話資訊
   */
  static async getSessionInfo(sessionId: string): Promise<SessionInfo> {
    const response: AxiosResponse<SessionInfo> = await apiClient.get(`/session/${sessionId}/info`);
    return response.data;
  }

  /**
   * 刪除會話
   */
  static async deleteSession(sessionId: string): Promise<{ message: string }> {
    const response = await apiClient.delete(`/session/${sessionId}`);
    return response.data;
  }

  /**
   * 取得系統統計
   */
  static async getSystemStats(): Promise<SystemStats> {
    const response: AxiosResponse<SystemStats> = await apiClient.get('/stats');
    return response.data;
  }

  /**
   * 取得服務資訊
   */
  static async getServiceInfo(): Promise<Record<string, any>> {
    const response = await apiClient.get('/');
    return response.data;
  }
}

// 工具函數
export const formatApiError = (error: ApiError): string => {
  if (error.error_code === 'NETWORK_ERROR') {
    return '網路連線錯誤，請檢查您的網路連線或確認 API 服務是否運行';
  }

  if (error.error_code === 'TIMEOUT_ERROR') {
    return '請求超時，請稍後再試';
  }

  return error.error_message;
};

// 檢查 API 連線狀態
export const checkApiConnection = async (): Promise<boolean> => {
  try {
    await FinanceAgentsAPI.healthCheck();
    return true;
  } catch (error) {
    console.error('API connection check failed:', error);
    return false;
  }
};

export default FinanceAgentsAPI;