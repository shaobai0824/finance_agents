import React, { useState } from 'react';
import styled from 'styled-components';
import { Settings, User, TrendingUp, DollarSign, Shield, X } from 'lucide-react';

import { UserProfile, RISK_TOLERANCE_LABELS, INCOME_LEVEL_LABELS } from '../../types';
import { theme, riskLevelColors } from '../../utils/theme';

interface UserProfilePanelProps {
  userProfile: UserProfile;
  onUpdateProfile: (profile: Partial<UserProfile>) => void;
  isOpen: boolean;
  onClose: () => void;
}

const Overlay = styled.div<{ isOpen: boolean }>`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  opacity: ${props => props.isOpen ? 1 : 0};
  visibility: ${props => props.isOpen ? 'visible' : 'hidden'};
  transition: all 0.3s ease;
`;

const Panel = styled.div<{ isOpen: boolean }>`
  position: fixed;
  right: 0;
  top: 0;
  bottom: 0;
  width: 400px;
  max-width: 90vw;
  background: white;
  box-shadow: ${theme.shadows.lg};
  z-index: 1001;
  transform: translateX(${props => props.isOpen ? '0' : '100%'});
  transition: transform 0.3s ease;
  overflow-y: auto;
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: ${theme.spacing.lg};
  border-bottom: 1px solid ${theme.colors.border};

  h2 {
    margin: 0;
    color: ${theme.colors.text.primary};
    font-size: 1.25rem;
    font-weight: 600;
  }
`;

const CloseButton = styled.button`
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  cursor: pointer;
  border-radius: ${theme.borderRadius.md};
  display: flex;
  align-items: center;
  justify-content: center;
  color: ${theme.colors.text.muted};
  transition: all 0.2s ease;

  &:hover {
    background: ${theme.colors.surface};
    color: ${theme.colors.text.primary};
  }
`;

const Content = styled.div`
  padding: ${theme.spacing.lg};
`;

const Section = styled.div`
  margin-bottom: ${theme.spacing.xl};

  &:last-child {
    margin-bottom: 0;
  }
`;

const SectionTitle = styled.h3`
  margin: 0 0 ${theme.spacing.md} 0;
  color: ${theme.colors.text.primary};
  font-size: 1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: ${theme.spacing.sm};

  svg {
    color: ${theme.colors.primary};
  }
`;

const FormGroup = styled.div`
  margin-bottom: ${theme.spacing.lg};
`;

const Label = styled.label`
  display: block;
  margin-bottom: ${theme.spacing.sm};
  color: ${theme.colors.text.secondary};
  font-weight: 500;
  font-size: 0.9rem;
`;

const Input = styled.input`
  width: 100%;
  padding: ${theme.spacing.md};
  border: 1px solid ${theme.colors.border};
  border-radius: ${theme.borderRadius.md};
  font-family: ${theme.fonts.body};
  font-size: 1rem;
  background: ${theme.colors.surface};
  transition: all 0.2s ease;

  &:focus {
    outline: none;
    border-color: ${theme.colors.primary};
    background: white;
    box-shadow: 0 0 0 3px ${theme.colors.primary}20;
  }
`;

const Select = styled.select`
  width: 100%;
  padding: ${theme.spacing.md};
  border: 1px solid ${theme.colors.border};
  border-radius: ${theme.borderRadius.md};
  font-family: ${theme.fonts.body};
  font-size: 1rem;
  background: white;
  cursor: pointer;
  transition: all 0.2s ease;

  &:focus {
    outline: none;
    border-color: ${theme.colors.primary};
    box-shadow: 0 0 0 3px ${theme.colors.primary}20;
  }
`;

const RiskLevelCard = styled.div<{ level: string; isSelected: boolean }>`
  padding: ${theme.spacing.md};
  border: 2px solid ${props => props.isSelected
    ? (riskLevelColors as Record<string, string>)[props.level] || theme.colors.border
    : theme.colors.border
  };
  border-radius: ${theme.borderRadius.md};
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: ${theme.spacing.sm};
  background: ${props => props.isSelected ? `${(riskLevelColors as Record<string, string>)[props.level] || theme.colors.primary}10` : 'white'};

  &:hover {
    border-color: ${props => (riskLevelColors as Record<string, string>)[props.level] || theme.colors.primary};
  }

  .title {
    font-weight: 600;
    color: ${theme.colors.text.primary};
    margin-bottom: ${theme.spacing.xs};
    display: flex;
    align-items: center;
    gap: ${theme.spacing.sm};
  }

  .description {
    font-size: 0.9rem;
    color: ${theme.colors.text.secondary};
    line-height: 1.4;
  }
`;

const CheckboxGroup = styled.div`
  display: grid;
  gap: ${theme.spacing.sm};
`;

const CheckboxItem = styled.label`
  display: flex;
  align-items: center;
  gap: ${theme.spacing.sm};
  cursor: pointer;
  padding: ${theme.spacing.sm};
  border-radius: ${theme.borderRadius.md};
  transition: background 0.2s ease;

  &:hover {
    background: ${theme.colors.surface};
  }

  input {
    margin: 0;
  }

  span {
    color: ${theme.colors.text.secondary};
    font-size: 0.9rem;
  }
`;

const Summary = styled.div`
  background: ${theme.colors.surface};
  border-radius: ${theme.borderRadius.md};
  padding: ${theme.spacing.md};
  margin-top: ${theme.spacing.lg};

  .title {
    font-weight: 600;
    color: ${theme.colors.text.primary};
    margin-bottom: ${theme.spacing.sm};
  }

  .item {
    display: flex;
    justify-content: space-between;
    margin-bottom: ${theme.spacing.xs};
    font-size: 0.9rem;

    .label {
      color: ${theme.colors.text.secondary};
    }

    .value {
      color: ${theme.colors.text.primary};
      font-weight: 500;
    }
  }
`;

const RISK_LEVEL_DESCRIPTIONS = {
  conservative: '追求資本保值，接受較低報酬，適合穩定收入需求',
  moderate: '平衡風險與報酬，適合大多數投資者',
  aggressive: '追求高報酬，能承受較大波動，適合長期投資'
};

const FINANCIAL_GOALS = [
  '退休規劃',
  '買房置產',
  '子女教育',
  '緊急基金',
  '財富增值',
  '創業資金',
  '旅遊基金',
  '醫療保障'
];

export const UserProfilePanel: React.FC<UserProfilePanelProps> = ({
  userProfile,
  onUpdateProfile,
  isOpen,
  onClose
}) => {
  const [localProfile, setLocalProfile] = useState<UserProfile>(userProfile);

  const handleUpdate = (updates: Partial<UserProfile>) => {
    const newProfile = { ...localProfile, ...updates };
    setLocalProfile(newProfile);
    onUpdateProfile(updates);
  };

  const handleGoalToggle = (goal: string) => {
    const currentGoals = localProfile.financial_goals || [];
    const newGoals = currentGoals.includes(goal)
      ? currentGoals.filter(g => g !== goal)
      : [...currentGoals, goal];

    handleUpdate({ financial_goals: newGoals });
  };

  return (
    <>
      <Overlay isOpen={isOpen} onClick={onClose} />
      <Panel isOpen={isOpen}>
        <Header>
          <h2>個人資料設定</h2>
          <CloseButton onClick={onClose}>
            <X size={20} />
          </CloseButton>
        </Header>

        <Content>
          {/* 基本資料 */}
          <Section>
            <SectionTitle>
              <User size={18} />
              基本資料
            </SectionTitle>

            <FormGroup>
              <Label>年齡</Label>
              <Input
                type="number"
                min="18"
                max="100"
                value={localProfile.age || ''}
                onChange={(e) => handleUpdate({ age: parseInt(e.target.value) || undefined })}
                placeholder="請輸入年齡"
              />
            </FormGroup>

            <FormGroup>
              <Label>收入水平</Label>
              <Select
                value={localProfile.income_level}
                onChange={(e) => handleUpdate({ income_level: e.target.value as any })}
              >
                {Object.entries(INCOME_LEVEL_LABELS).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </Select>
            </FormGroup>

            <FormGroup>
              <Label>投資經驗</Label>
              <Select
                value={localProfile.investment_experience || 'beginner'}
                onChange={(e) => handleUpdate({ investment_experience: e.target.value as any })}
              >
                <option value="beginner">初學者</option>
                <option value="intermediate">有一些經驗</option>
                <option value="advanced">經驗豐富</option>
              </Select>
            </FormGroup>
          </Section>

          {/* 風險偏好 */}
          <Section>
            <SectionTitle>
              <Shield size={18} />
              風險偏好
            </SectionTitle>

            {Object.entries(RISK_TOLERANCE_LABELS).map(([key, label]) => (
              <RiskLevelCard
                key={key}
                level={key}
                isSelected={localProfile.risk_tolerance === key}
                onClick={() => handleUpdate({ risk_tolerance: key as any })}
              >
                <div className="title">
                  <TrendingUp size={16} />
                  {label}
                </div>
                <div className="description">
                  {RISK_LEVEL_DESCRIPTIONS[key as keyof typeof RISK_LEVEL_DESCRIPTIONS]}
                </div>
              </RiskLevelCard>
            ))}
          </Section>

          {/* 理財目標 */}
          <Section>
            <SectionTitle>
              <DollarSign size={18} />
              理財目標
            </SectionTitle>

            <CheckboxGroup>
              {FINANCIAL_GOALS.map((goal) => (
                <CheckboxItem key={goal}>
                  <input
                    type="checkbox"
                    checked={(localProfile.financial_goals || []).includes(goal)}
                    onChange={() => handleGoalToggle(goal)}
                  />
                  <span>{goal}</span>
                </CheckboxItem>
              ))}
            </CheckboxGroup>
          </Section>

          {/* 資料摘要 */}
          <Summary>
            <div className="title">資料摘要</div>

            <div className="item">
              <span className="label">年齡</span>
              <span className="value">{localProfile.age || '未設定'} 歲</span>
            </div>

            <div className="item">
              <span className="label">收入水平</span>
              <span className="value">{INCOME_LEVEL_LABELS[localProfile.income_level]}</span>
            </div>

            <div className="item">
              <span className="label">風險偏好</span>
              <span className="value">{RISK_TOLERANCE_LABELS[localProfile.risk_tolerance]}</span>
            </div>

            <div className="item">
              <span className="label">投資經驗</span>
              <span className="value">
                {localProfile.investment_experience === 'beginner' && '初學者'}
                {localProfile.investment_experience === 'intermediate' && '有一些經驗'}
                {localProfile.investment_experience === 'advanced' && '經驗豐富'}
              </span>
            </div>

            <div className="item">
              <span className="label">理財目標</span>
              <span className="value">
                {(localProfile.financial_goals?.length || 0)} 項
              </span>
            </div>
          </Summary>
        </Content>
      </Panel>
    </>
  );
};