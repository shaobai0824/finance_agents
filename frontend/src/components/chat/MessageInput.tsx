import React, { useState, useRef, useEffect } from 'react';
import styled from 'styled-components';
import { Send, Loader2 } from 'lucide-react';

import { theme } from '../../utils/theme';

interface MessageInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  placeholder?: string;
}

const InputContainer = styled.div`
  display: flex;
  gap: ${theme.spacing.sm};
  padding: ${theme.spacing.lg};
  background: white;
  border-top: 1px solid ${theme.colors.border};
  align-items: flex-end;
`;

const InputWrapper = styled.div`
  flex: 1;
  position: relative;
`;

const TextArea = styled.textarea`
  width: 100%;
  min-height: 44px;
  max-height: 120px;
  padding: ${theme.spacing.md} ${theme.spacing.lg};
  border: 1px solid ${theme.colors.border};
  border-radius: ${theme.borderRadius.lg};
  font-family: ${theme.fonts.body};
  font-size: 1rem;
  line-height: 1.4;
  resize: none;
  outline: none;
  background: ${theme.colors.surface};
  transition: all 0.2s ease;

  &:focus {
    border-color: ${theme.colors.primary};
    background: white;
    box-shadow: 0 0 0 3px ${theme.colors.primary}20;
  }

  &::placeholder {
    color: ${theme.colors.text.muted};
  }

  &:disabled {
    background: ${theme.colors.surface};
    color: ${theme.colors.text.muted};
    cursor: not-allowed;
  }
`;

const SendButton = styled.button<{ isDisabled: boolean }>`
  width: 44px;
  height: 44px;
  border: none;
  border-radius: ${theme.borderRadius.lg};
  background: ${theme.colors.primary};
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;

  &:hover:not(:disabled) {
    background: ${theme.colors.primary}dd;
    transform: translateY(-1px);
  }

  &:active:not(:disabled) {
    transform: translateY(0);
  }

  &:disabled {
    background: ${theme.colors.text.muted};
    cursor: not-allowed;
    transform: none;
  }

  ${props => props.isDisabled && `
    background: ${theme.colors.text.muted};
    cursor: not-allowed;
  `}
`;

const CharacterCount = styled.div<{ isNearLimit: boolean }>`
  position: absolute;
  bottom: 8px;
  right: 12px;
  font-size: 0.75rem;
  color: ${props => props.isNearLimit ? theme.colors.warning : theme.colors.text.muted};
  background: white;
  padding: 2px 4px;
  border-radius: ${theme.borderRadius.sm};
`;

const QuickActions = styled.div`
  display: flex;
  gap: ${theme.spacing.xs};
  margin-bottom: ${theme.spacing.sm};
  overflow-x: auto;
  padding: 0 ${theme.spacing.lg};

  &::-webkit-scrollbar {
    display: none;
  }
`;

const QuickActionButton = styled.button`
  padding: ${theme.spacing.xs} ${theme.spacing.sm};
  border: 1px solid ${theme.colors.border};
  border-radius: ${theme.borderRadius.full};
  background: white;
  color: ${theme.colors.text.secondary};
  font-size: 0.85rem;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease;

  &:hover {
    border-color: ${theme.colors.primary};
    color: ${theme.colors.primary};
  }

  &:active {
    background: ${theme.colors.primary}10;
  }
`;

const MAX_MESSAGE_LENGTH = 2000;

const QUICK_ACTIONS = [
  '我想要投資建議',
  '市場分析報告',
  '風險評估',
  '退休規劃',
  '股票推薦',
  '法律合規問題',
];

export const MessageInput: React.FC<MessageInputProps> = ({
  onSendMessage,
  isLoading,
  placeholder = '輸入您的理財問題...'
}) => {
  const [message, setMessage] = useState('');
  const textAreaRef = useRef<HTMLTextAreaElement>(null);

  // 自動調整高度
  useEffect(() => {
    const textArea = textAreaRef.current;
    if (textArea) {
      textArea.style.height = 'auto';
      textArea.style.height = `${textArea.scrollHeight}px`;
    }
  }, [message]);

  // 處理發送
  const handleSend = () => {
    const trimmedMessage = message.trim();
    if (trimmedMessage && !isLoading) {
      onSendMessage(trimmedMessage);
      setMessage('');
    }
  };

  // 處理鍵盤事件
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // 處理快速動作
  const handleQuickAction = (action: string) => {
    if (!isLoading) {
      onSendMessage(action);
    }
  };

  const isNearLimit = message.length > MAX_MESSAGE_LENGTH * 0.8;
  const isOverLimit = message.length > MAX_MESSAGE_LENGTH;
  const canSend = message.trim().length > 0 && !isLoading && !isOverLimit;

  return (
    <>
      <QuickActions>
        {QUICK_ACTIONS.map((action, index) => (
          <QuickActionButton
            key={index}
            onClick={() => handleQuickAction(action)}
            disabled={isLoading}
          >
            {action}
          </QuickActionButton>
        ))}
      </QuickActions>

      <InputContainer>
        <InputWrapper>
          <TextArea
            ref={textAreaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={isLoading}
            maxLength={MAX_MESSAGE_LENGTH}
          />

          {message.length > 0 && (
            <CharacterCount isNearLimit={isNearLimit}>
              {message.length}/{MAX_MESSAGE_LENGTH}
            </CharacterCount>
          )}
        </InputWrapper>

        <SendButton
          onClick={handleSend}
          disabled={!canSend}
          isDisabled={!canSend}
          title={isLoading ? '處理中...' : '發送訊息 (Enter)'}
        >
          {isLoading ? (
            <Loader2 size={20} className="animate-spin" />
          ) : (
            <Send size={20} />
          )}
        </SendButton>
      </InputContainer>
    </>
  );
};