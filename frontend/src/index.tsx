import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';

// 錯誤邊界組件
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('應用程式錯誤:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '2rem',
          textAlign: 'center',
          backgroundColor: '#f8f9fa',
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          fontFamily: 'Inter, sans-serif'
        }}>
          <h1 style={{ color: '#dc3545', marginBottom: '1rem' }}>
            應用程式發生錯誤
          </h1>
          <p style={{ color: '#6c757d', marginBottom: '1rem' }}>
            抱歉，應用程式遇到了一個錯誤。請重新載入頁面或聯繫技術支援。
          </p>
          <details style={{ marginTop: '1rem', textAlign: 'left' }}>
            <summary style={{ cursor: 'pointer', color: '#007bff' }}>
              顯示技術詳情
            </summary>
            <pre style={{
              backgroundColor: '#f8f9fa',
              padding: '1rem',
              border: '1px solid #dee2e6',
              borderRadius: '4px',
              marginTop: '0.5rem',
              overflow: 'auto',
              fontSize: '0.85rem'
            }}>
              {this.state.error?.stack}
            </pre>
          </details>
          <button
            onClick={() => window.location.reload()}
            style={{
              marginTop: '1rem',
              padding: '0.5rem 1rem',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            重新載入頁面
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

// 主要渲染邏輯
const container = document.getElementById('root');
if (!container) {
  throw new Error('找不到根元素 #root');
}

const root = createRoot(container);

// 開發模式警告
if (process.env.NODE_ENV === 'development') {
  console.info('🚀 Finance Agents 前端已啟動（開發模式）');
  console.info('📡 API 代理伺服器:', process.env.REACT_APP_API_URL || 'http://localhost:8000');
}

// 渲染應用
root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);

// 服務工作者註冊（PWA 支援）
if ('serviceWorker' in navigator && process.env.NODE_ENV === 'production') {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then((registration) => {
        console.info('SW 註冊成功:', registration.scope);
      })
      .catch((error) => {
        console.warn('SW 註冊失敗:', error);
      });
  });
}