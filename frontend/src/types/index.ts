// API 類型定義（與後端保持一致）

export interface UserProfile {
  age?: number;
  risk_tolerance: 'conservative' | 'moderate' | 'aggressive';
  income_level: 'low' | 'middle' | 'high';
  investment_experience?: 'beginner' | 'intermediate' | 'advanced';
  financial_goals?: string[];
}

export interface QueryRequest {
  query: string;
  user_profile: UserProfile;
  session_id?: string;
}

export interface ExpertResponse {
  expert_type: string;
  content: string;
  confidence: number;
  sources: string[];
  metadata?: Record<string, any>;
}

export interface QueryResponse {
  session_id: string;
  query: string;
  final_response: string;
  confidence_score: number;
  expert_responses: ExpertResponse[];
  sources: string[];
  processing_time: number;
  status: string;
}

export interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  services: Record<string, string>;
}

export interface SessionInfo {
  session_id: string;
  created_at: string;
  last_activity: string;
  query_count: number;
  status: string;
}

// 前端特定類型

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  expert_responses?: ExpertResponse[];
  confidence_score?: number;
  processing_time?: number;
  sources?: string[];
  loading?: boolean;
}

export interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  sessionId: string | null;
  userProfile: UserProfile;
  error: string | null;
}

export interface SystemStats {
  active_sessions: number;
  total_queries: number;
  system_status: string;
  vector_store?: {
    document_count: number;
    collection_name: string;
  };
  knowledge_retriever?: Record<string, any>;
}

export interface ApiError {
  error_code: string;
  error_message: string;
  details?: Record<string, any>;
}

// UI 組件類型

export interface ThemeColors {
  primary: string;
  secondary: string;
  success: string;
  warning: string;
  error: string;
  info: string;
  background: string;
  surface: string;
  text: {
    primary: string;
    secondary: string;
    muted: string;
  };
  border: string;
}

export interface Theme {
  colors: ThemeColors;
  fonts: {
    body: string;
    heading: string;
    monospace: string;
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    xxl: string;
  };
  borderRadius: {
    sm: string;
    md: string;
    lg: string;
    full: string;
  };
  shadows: {
    sm: string;
    md: string;
    lg: string;
  };
  breakpoints: {
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
}

// 專家類型映射（用於顯示）
export const EXPERT_TYPE_LABELS: Record<string, string> = {
  'financial_planner': '理財規劃專家',
  'financial_analyst': '金融分析專家',
  'legal_expert': '法律合規專家',
  'manager': '智能路由管理員'
};

// 風險等級標籤
export const RISK_TOLERANCE_LABELS: Record<string, string> = {
  'conservative': '保守型',
  'moderate': '穩健型',
  'aggressive': '積極型'
};

// 收入水平標籤
export const INCOME_LEVEL_LABELS: Record<string, string> = {
  'low': '較低收入',
  'middle': '中等收入',
  'high': '較高收入'
};