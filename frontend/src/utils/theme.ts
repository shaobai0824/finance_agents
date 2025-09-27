import { Theme } from '../types';

// 主題色彩定義
export const theme: Theme = {
  colors: {
    primary: '#2563eb',      // 藍色 - 信任、專業
    secondary: '#64748b',    // 灰藍色 - 穩定
    success: '#16a34a',      // 綠色 - 成功、成長
    warning: '#d97706',      // 橙色 - 警告
    error: '#dc2626',        // 紅色 - 錯誤、風險
    info: '#0891b2',         // 青色 - 資訊
    background: '#ffffff',   // 白色背景
    surface: '#f8fafc',      // 淺灰表面
    text: {
      primary: '#0f172a',    // 深灰文字
      secondary: '#475569',  // 中灰文字
      muted: '#94a3b8',      // 淺灰文字
    },
    border: '#e2e8f0',       // 邊框色
  },
  fonts: {
    body: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    heading: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    monospace: "'Fira Code', 'Monaco', 'Cascadia Code', monospace",
  },
  spacing: {
    xs: '0.25rem',    // 4px
    sm: '0.5rem',     // 8px
    md: '1rem',       // 16px
    lg: '1.5rem',     // 24px
    xl: '2rem',       // 32px
    xxl: '3rem',      // 48px
  },
  borderRadius: {
    sm: '0.25rem',    // 4px
    md: '0.5rem',     // 8px
    lg: '0.75rem',    // 12px
    full: '9999px',   // 圓形
  },
  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  },
  breakpoints: {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
  },
};

// 深色主題（可選）
export const darkTheme: Theme = {
  ...theme,
  colors: {
    ...theme.colors,
    background: '#0f172a',
    surface: '#1e293b',
    text: {
      primary: '#f1f5f9',
      secondary: '#cbd5e1',
      muted: '#64748b',
    },
    border: '#334155',
  },
};

// 主題工具函數
export const getTheme = (isDark: boolean = false): Theme => {
  return isDark ? darkTheme : theme;
};

// 專家類型色彩映射
export const expertColors = {
  'financial_planner': '#16a34a',   // 綠色 - 理財規劃
  'financial_analyst': '#2563eb',   // 藍色 - 金融分析
  'legal_expert': '#dc2626',        // 紅色 - 法律合規
  'manager': '#64748b',             // 灰色 - 管理員
};

// 風險等級色彩
export const riskLevelColors = {
  'conservative': '#16a34a',  // 綠色 - 保守
  'moderate': '#d97706',      // 橙色 - 穩健
  'aggressive': '#dc2626',    // 紅色 - 積極
};

// 信心度色彩計算
export const getConfidenceColor = (confidence: number): string => {
  if (confidence >= 0.8) return theme.colors.success;
  if (confidence >= 0.6) return theme.colors.warning;
  return theme.colors.error;
};