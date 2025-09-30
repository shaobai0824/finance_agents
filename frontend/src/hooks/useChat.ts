import { useState, useCallback, useRef, useEffect } from 'react';
import { toast } from 'react-toastify';
import { v4 as uuidv4 } from 'uuid';

import {
  ChatState,
  ChatMessage,
  UserProfile,
  QueryRequest,
  ApiError
} from '../types';
import { FinanceAgentsAPI, formatApiError } from '../services/api';

// 初始狀態
const initialState: ChatState = {
  messages: [],
  isLoading: false,
  sessionId: null,
  userProfile: {
    risk_tolerance: 'moderate',
    income_level: 'middle',
  },
  error: null,
};

// 歡迎訊息
const welcomeMessage: ChatMessage = {
  id: uuidv4(),
  type: 'assistant',
  content: `👋 歡迎使用 Finance Agents 智能理財諮詢系統！

我是您的專業理財顧問團隊，包含：
• 💰 **理財規劃專家** - 個人投資建議與資產配置
• 📊 **金融分析專家** - 市場分析與股票研究
• ⚖️ **法律合規專家** - 投資法規與風險提醒

請告訴我您的理財問題，我會為您提供專業的建議！`,
  timestamp: new Date(),
};

export const useChat = () => {
  const [state, setState] = useState<ChatState>({
    ...initialState,
    messages: [welcomeMessage],
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自動滾動到最新訊息
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [state.messages, scrollToBottom]);

  // 更新用戶資料
  const updateUserProfile = useCallback((profile: Partial<UserProfile>) => {
    setState(prev => ({
      ...prev,
      userProfile: { ...prev.userProfile, ...profile },
    }));
  }, []);

  // 添加訊息到聊天記錄
  const addMessage = useCallback((message: Omit<ChatMessage, 'id' | 'timestamp'>) => {
    const newMessage: ChatMessage = {
      ...message,
      id: uuidv4(),
      timestamp: new Date(),
    };

    setState(prev => ({
      ...prev,
      messages: [...prev.messages, newMessage],
    }));

    return newMessage.id;
  }, []);

  // 更新特定訊息
  const updateMessage = useCallback((id: string, updates: Partial<ChatMessage>) => {
    setState(prev => ({
      ...prev,
      messages: prev.messages.map(msg =>
        msg.id === id ? { ...msg, ...updates } : msg
      ),
    }));
  }, []);

  // 發送查詢
  const sendQuery = useCallback(async (query: string) => {
    if (!query.trim()) {
      toast.error('請輸入您的理財問題');
      return;
    }

    // 添加用戶訊息
    const userMessageId = addMessage({
      type: 'user',
      content: query,
    });

    // 添加載入中的助手訊息
    const assistantMessageId = addMessage({
      type: 'assistant',
      content: '正在分析您的問題，請稍候...',
      loading: true,
    });

    // 設定載入狀態
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      // 構建對話歷史（排除當前查詢和載入訊息）
      const conversationHistory = state.messages
        .filter(msg => !msg.loading && msg.type !== 'system')  // 排除載入訊息和系統訊息
        .map(msg => ({
          role: msg.type as 'user' | 'assistant',
          content: msg.content,
          timestamp: msg.timestamp.toISOString()
        }));

      // 準備 API 請求
      const request: QueryRequest = {
        query: query.trim(),
        user_profile: state.userProfile,
        session_id: state.sessionId || undefined,
        conversation_history: conversationHistory.length > 0 ? conversationHistory : undefined,
      };

      // 發送 API 請求
      const response = await FinanceAgentsAPI.sendQuery(request);

      // 更新會話 ID
      if (!state.sessionId) {
        setState(prev => ({ ...prev, sessionId: response.session_id }));
      }

      // 直接使用後端回應，避免重複內容
      let formattedContent = response.final_response;

      // 添加處理時間和來源資訊
      if (response.processing_time) {
        formattedContent += `\n*處理時間: ${response.processing_time.toFixed(2)}秒*`;
      }

      if (response.sources.length > 0) {
        formattedContent += `\n*資料來源: ${response.sources.join(', ')}*`;
      }

      // 更新助手訊息
      updateMessage(assistantMessageId, {
        content: formattedContent,
        loading: false,
        expert_responses: response.expert_responses,
        confidence_score: response.confidence_score,
        processing_time: response.processing_time,
        sources: response.sources,
      });

      toast.success('分析完成！');

    } catch (error) {
      console.error('Query failed:', error);

      const apiError = error as ApiError;
      const errorMessage = formatApiError(apiError);

      // 更新助手訊息顯示錯誤
      updateMessage(assistantMessageId, {
        content: `❌ 抱歉，處理您的請求時發生錯誤：\n\n${errorMessage}\n\n請檢查網路連線或稍後再試。`,
        loading: false,
      });

      setState(prev => ({ ...prev, error: errorMessage }));
      toast.error(errorMessage);
    } finally {
      setState(prev => ({ ...prev, isLoading: false }));
    }
  }, [state.userProfile, state.sessionId, addMessage, updateMessage]);

  // 清除聊天記錄
  const clearChat = useCallback(async () => {
    try {
      // 如果有會話 ID，嘗試刪除會話
      if (state.sessionId) {
        await FinanceAgentsAPI.deleteSession(state.sessionId);
      }
    } catch (error) {
      console.warn('Failed to delete session:', error);
    }

    // 重置狀態
    setState({
      ...initialState,
      messages: [welcomeMessage],
    });

    toast.info('聊天記錄已清除');
  }, [state.sessionId]);

  // 重新發送最後一條訊息
  const retryLastMessage = useCallback(() => {
    const lastUserMessage = state.messages
      .filter(msg => msg.type === 'user')
      .pop();

    if (lastUserMessage) {
      sendQuery(lastUserMessage.content);
    }
  }, [state.messages, sendQuery]);

  return {
    // 狀態
    messages: state.messages,
    isLoading: state.isLoading,
    sessionId: state.sessionId,
    userProfile: state.userProfile,
    error: state.error,

    // 動作
    sendQuery,
    clearChat,
    retryLastMessage,
    updateUserProfile,

    // Refs
    messagesEndRef,
  };
};

// 工具函數：取得專家圖示
const getExpertIcon = (expertType: string): string => {
  const icons: Record<string, string> = {
    'financial_planner': '💰',
    'financial_analyst': '📊',
    'legal_expert': '⚖️',
    'manager': '🤖',
  };
  return icons[expertType] || '👨‍💼';
};