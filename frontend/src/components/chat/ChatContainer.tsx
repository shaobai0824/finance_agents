import React from 'react';
import styled from 'styled-components';

import { MessageBubble } from './MessageBubble';
import { MessageInput } from './MessageInput';
import { useChat } from '../../hooks/useChat';
import { theme } from '../../utils/theme';

interface ChatContainerProps {
  className?: string;
}

const Container = styled.div`
  display: flex;
  flex-direction: column;
  height: 100%;
  background: ${theme.colors.background};
`;

const MessagesArea = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: ${theme.spacing.lg};
  display: flex;
  flex-direction: column;
  gap: ${theme.spacing.md};

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: ${theme.colors.surface};
  }

  &::-webkit-scrollbar-thumb {
    background: ${theme.colors.border};
    border-radius: ${theme.borderRadius.full};

    &:hover {
      background: ${theme.colors.text.muted};
    }
  }
`;

const EmptyState = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: ${theme.colors.text.muted};
  text-align: center;
  padding: ${theme.spacing.xl};

  .icon {
    font-size: 3rem;
    margin-bottom: ${theme.spacing.lg};
  }

  h3 {
    margin: 0 0 ${theme.spacing.sm} 0;
    color: ${theme.colors.text.secondary};
    font-weight: 600;
  }

  p {
    margin: 0;
    font-size: 0.9rem;
    line-height: 1.5;
  }
`;

const MessagesEndRef = styled.div`
  height: 1px;
`;

const ConnectionStatus = styled.div<{ isConnected: boolean }>`
  padding: ${theme.spacing.sm} ${theme.spacing.lg};
  background: ${props => props.isConnected ? theme.colors.success : theme.colors.error};
  color: white;
  text-align: center;
  font-size: 0.85rem;
  display: ${props => props.isConnected ? 'none' : 'block'};
`;

const LoadingOverlay = styled.div<{ show: boolean }>`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: ${props => props.show ? 'flex' : 'none'};
  align-items: center;
  justify-content: center;
  z-index: 10;

  .spinner {
    width: 40px;
    height: 40px;
    border: 3px solid ${theme.colors.surface};
    border-top: 3px solid ${theme.colors.primary};
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

export const ChatContainer: React.FC<ChatContainerProps> = ({ className }) => {
  const {
    messages,
    isLoading,
    sendQuery,
    messagesEndRef,
    error
  } = useChat();

  const hasMessages = messages.length > 0;

  return (
    <Container className={className}>
      <ConnectionStatus isConnected={!error}>
        {error ? `連線錯誤: ${error}` : '已連線'}
      </ConnectionStatus>

      <MessagesArea>
        {hasMessages ? (
          <>
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            <MessagesEndRef ref={messagesEndRef} />
          </>
        ) : (
          <EmptyState>
            <div className="icon">💬</div>
            <h3>開始您的理財諮詢</h3>
            <p>
              歡迎使用 Finance Agents 智能理財系統<br />
              請輸入您的理財問題，我們的專家團隊將為您提供專業建議
            </p>
          </EmptyState>
        )}
      </MessagesArea>

      <MessageInput
        onSendMessage={sendQuery}
        isLoading={isLoading}
        placeholder="請輸入您的理財問題..."
      />

      <LoadingOverlay show={isLoading && !hasMessages}>
        <div className="spinner" />
      </LoadingOverlay>
    </Container>
  );
};