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
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

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
   * 發送理財諮詢查詢（普通模式）
   */
  static async sendQuery(request: QueryRequest): Promise<QueryResponse> {
    const response: AxiosResponse<QueryResponse> = await apiClient.post('/query', request);
    return response.data;
  }

  /**
   * 發送理財諮詢查詢（流式模式）
   * 使用 EventSource (SSE) 接收逐塊回應
   *
   * @param request 查詢請求
   * @param onChunk 接收到新內容塊的回調函數
   * @param onDone 完成時的回調函數
   * @param onError 錯誤時的回調函數
   * @returns EventSource 實例（可用於取消請求）
   */
  static sendQueryStream(
    request: QueryRequest,
    onChunk: (content: string) => void,
    onDone: (sessionId: string) => void,
    onError: (error: string) => void
  ): EventSource {
    // 構建 URL 和查詢參數
    const url = new URL(`${API_BASE_URL}/query/stream`);

    // 由於 EventSource 只支援 GET，我們需要使用 fetch + ReadableStream
    // 或者使用 POST with fetch 的 EventSource polyfill
    // 這裡採用原生 fetch + SSE 手動解析

    // 創建 AbortController 以支援取消
    const controller = new AbortController();

    // 使用 fetch 發送 POST 請求
    fetch(`${API_BASE_URL}/query/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify(request),
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error('無法讀取回應流');
        }

        // 讀取流
        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            break;
          }

          // 解碼並解析 SSE 數據
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6); // 移除 'data: ' 前綴

              try {
                const event = JSON.parse(data);

                switch (event.type) {
                  case 'start':
                    console.log('Stream started:', event.session_id);
                    break;
                  case 'content':
                    onChunk(event.content);
                    break;
                  case 'done':
                    onDone(event.session_id);
                    break;
                  case 'error':
                    onError(event.error);
                    break;
                }
              } catch (e) {
                console.error('Failed to parse SSE data:', data, e);
              }
            }
          }
        }
      })
      .catch((error) => {
        if (error.name === 'AbortError') {
          console.log('Stream aborted');
        } else {
          console.error('Stream error:', error);
          onError(error.message || '流式請求失敗');
        }
      });

    // 返回一個可用於取消的對象（模擬 EventSource 接口）
    return {
      close: () => controller.abort(),
      readyState: 1, // OPEN
    } as EventSource;
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