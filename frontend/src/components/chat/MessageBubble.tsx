import React from 'react';
import styled from 'styled-components';
import ReactMarkdown from 'react-markdown';
import { format } from 'date-fns';
import { User, Bot, Clock, TrendingUp } from 'lucide-react';

import { ChatMessage, ExpertResponse } from '../../types';
import { theme, getConfidenceColor, expertColors } from '../../utils/theme';

interface MessageBubbleProps {
  message: ChatMessage;
}

const MessageContainer = styled.div<{ isUser: boolean }>`
  display: flex;
  gap: ${theme.spacing.md};
  margin-bottom: ${theme.spacing.lg};
  align-items: flex-start;

  ${props => props.isUser && `
    flex-direction: row-reverse;
  `}
`;

const Avatar = styled.div<{ isUser: boolean }>`
  width: 40px;
  height: 40px;
  border-radius: ${theme.borderRadius.full};
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  ${props => props.isUser ? `
    background: ${theme.colors.primary};
    color: white;
  ` : `
    background: ${theme.colors.surface};
    color: ${theme.colors.text.secondary};
    border: 1px solid ${theme.colors.border};
  `}
`;

const MessageContent = styled.div<{ isUser: boolean }>`
  max-width: 70%;
  min-width: 200px;

  @media (max-width: ${theme.breakpoints.md}) {
    max-width: 85%;
    min-width: auto;
  }
`;

const MessageBubbleStyled = styled.div<{ isUser: boolean; isLoading?: boolean }>`
  padding: ${theme.spacing.md} ${theme.spacing.lg};
  border-radius: ${theme.borderRadius.lg};
  box-shadow: ${theme.shadows.sm};
  position: relative;

  ${props => props.isUser ? `
    background: ${theme.colors.primary};
    color: white;
    border-bottom-right-radius: ${theme.spacing.sm};
  ` : `
    background: white;
    color: ${theme.colors.text.primary};
    border: 1px solid ${theme.colors.border};
    border-bottom-left-radius: ${theme.spacing.sm};
  `}

  ${props => props.isLoading && `
    &::after {
      content: '';
      position: absolute;
      bottom: 8px;
      right: 12px;
      width: 12px;
      height: 12px;
      border: 2px solid ${theme.colors.text.muted};
      border-top: 2px solid ${theme.colors.primary};
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }

    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  `}
`;

const MessageText = styled.div`
  line-height: 1.6;

  p {
    margin: 0 0 ${theme.spacing.sm} 0;

    &:last-child {
      margin-bottom: 0;
    }
  }

  h3, h4 {
    margin: ${theme.spacing.md} 0 ${theme.spacing.sm} 0;
    color: ${theme.colors.text.primary};
  }

  ul, ol {
    margin: ${theme.spacing.sm} 0;
    padding-left: ${theme.spacing.lg};
  }

  li {
    margin-bottom: ${theme.spacing.xs};
  }

  strong {
    font-weight: 600;
  }

  code {
    background: ${theme.colors.surface};
    padding: 2px 4px;
    border-radius: ${theme.spacing.xs};
    font-family: ${theme.fonts.monospace};
    font-size: 0.9em;
  }

  hr {
    border: none;
    border-top: 1px solid ${theme.colors.border};
    margin: ${theme.spacing.md} 0;
  }
`;

const MessageMeta = styled.div`
  display: flex;
  align-items: center;
  gap: ${theme.spacing.sm};
  margin-top: ${theme.spacing.sm};
  font-size: 0.85rem;
  color: ${theme.colors.text.muted};
`;

const ExpertBadge = styled.div<{ expertType: string }>`
  display: inline-flex;
  align-items: center;
  gap: ${theme.spacing.xs};
  padding: ${theme.spacing.xs} ${theme.spacing.sm};
  background: ${props => (expertColors as Record<string, string>)[props.expertType] || theme.colors.secondary}20;
  color: ${props => (expertColors as Record<string, string>)[props.expertType] || theme.colors.secondary};
  border-radius: ${theme.borderRadius.full};
  font-size: 0.8rem;
  font-weight: 500;
  margin: ${theme.spacing.xs} ${theme.spacing.xs} 0 0;
`;

const ConfidenceBar = styled.div<{ confidence: number }>`
  display: flex;
  align-items: center;
  gap: ${theme.spacing.xs};
  font-size: 0.8rem;

  .bar {
    width: 40px;
    height: 4px;
    background: ${theme.colors.surface};
    border-radius: ${theme.borderRadius.full};
    overflow: hidden;

    .fill {
      height: 100%;
      background: ${props => getConfidenceColor(props.confidence)};
      width: ${props => props.confidence * 100}%;
      transition: width 0.3s ease;
    }
  }
`;

const LoadingDots = styled.div`
  display: inline-flex;
  gap: 2px;

  .dot {
    width: 6px;
    height: 6px;
    background: ${theme.colors.text.muted};
    border-radius: 50%;
    animation: bounce 1.4s infinite ease-in-out both;

    &:nth-child(1) { animation-delay: -0.32s; }
    &:nth-child(2) { animation-delay: -0.16s; }
  }

  @keyframes bounce {
    0%, 80%, 100% {
      transform: scale(0);
    } 40% {
      transform: scale(1);
    }
  }
`;

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.type === 'user';
  const isSystem = message.type === 'system';

  const formatTime = (date: Date) => {
    return format(date, 'HH:mm');
  };

  if (isSystem) {
    return (
      <MessageContainer isUser={false}>
        <SystemMessage>{message.content}</SystemMessage>
      </MessageContainer>
    );
  }

  return (
    <MessageContainer isUser={isUser}>
      <Avatar isUser={isUser}>
        {isUser ? <User size={20} /> : <Bot size={20} />}
      </Avatar>

      <MessageContent isUser={isUser}>
        <MessageBubbleStyled isUser={isUser} isLoading={message.loading}>
          <MessageText>
            {message.loading ? (
              <div>
                {message.content}
                <LoadingDots>
                  <div className="dot" />
                  <div className="dot" />
                  <div className="dot" />
                </LoadingDots>
              </div>
            ) : (
              <ReactMarkdown>{message.content}</ReactMarkdown>
            )}
          </MessageText>

          {!message.loading && (
            <MessageMeta>
              <Clock size={12} />
              <span>{formatTime(message.timestamp)}</span>

              {message.confidence_score && (
                <ConfidenceBar confidence={message.confidence_score}>
                  <TrendingUp size={12} />
                  <div className="bar">
                    <div className="fill" />
                  </div>
                  <span>{(message.confidence_score * 100).toFixed(0)}%</span>
                </ConfidenceBar>
              )}

              {message.processing_time && (
                <span>• {message.processing_time.toFixed(2)}s</span>
              )}
            </MessageMeta>
          )}
        </MessageBubbleStyled>

        {/* 專家回應標籤 */}
        {message.expert_responses && message.expert_responses.length > 0 && (
          <div style={{ marginTop: theme.spacing.sm }}>
            {message.expert_responses.map((expert, index) => (
              <ExpertBadge key={index} expertType={expert.expert_type}>
                {getExpertIcon(expert.expert_type)} {expert.expert_type}專家
              </ExpertBadge>
            ))}
          </div>
        )}
      </MessageContent>
    </MessageContainer>
  );
};

const SystemMessage = styled.div`
  text-align: center;
  padding: ${theme.spacing.sm} ${theme.spacing.md};
  background: ${theme.colors.surface};
  color: ${theme.colors.text.muted};
  border-radius: ${theme.borderRadius.md};
  font-size: 0.9rem;
  margin: ${theme.spacing.md} auto;
  max-width: 400px;
`;

// 工具函數
const getExpertIcon = (expertType: string): string => {
  const icons: Record<string, string> = {
    'financial_planner': '💰',
    'financial_analyst': '📊',
    'legal_expert': '⚖️',
    'manager': '🤖',
  };
  return icons[expertType] || '👨‍💼';
};