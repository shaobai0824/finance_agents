import React from 'react';
import styled, { ThemeProvider, createGlobalStyle } from 'styled-components';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import { ChatContainer } from './components/chat/ChatContainer';
import { UserProfilePanel } from './components/layout/UserProfilePanel';
import { useChat } from './hooks/useChat';
import { theme } from './utils/theme';

const GlobalStyle = createGlobalStyle`
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  html, body, #root {
    height: 100%;
    font-family: ${theme.fonts.body};
    background: ${theme.colors.background};
    color: ${theme.colors.text.primary};
  }

  body {
    overflow: hidden;
  }

  /* 自定義滾動條 */
  ::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }

  ::-webkit-scrollbar-track {
    background: ${theme.colors.surface};
  }

  ::-webkit-scrollbar-thumb {
    background: ${theme.colors.border};
    border-radius: ${theme.borderRadius.full};
  }

  ::-webkit-scrollbar-thumb:hover {
    background: ${theme.colors.text.muted};
  }
`;

const AppContainer = styled.div`
  display: flex;
  height: 100vh;
  background: ${theme.colors.background};
`;

const MainContent = styled.main`
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0; /* 防止 flex 項目溢出 */
`;

const Header = styled.header`
  background: ${theme.colors.surface};
  border-bottom: 1px solid ${theme.colors.border};
  padding: ${theme.spacing.md} ${theme.spacing.lg};
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

const Logo = styled.div`
  display: flex;
  align-items: center;
  gap: ${theme.spacing.sm};

  .icon {
    font-size: 1.5rem;
  }

  .text {
    font-size: 1.2rem;
    font-weight: 600;
    color: ${theme.colors.text.primary};
  }
`;

const SystemStatus = styled.div`
  display: flex;
  align-items: center;
  gap: ${theme.spacing.sm};
  font-size: 0.85rem;
  color: ${theme.colors.text.muted};

  .status-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: ${theme.colors.success};
  }
`;

const ChatArea = styled.div`
  flex: 1;
  display: flex;
  min-height: 0;
`;

const SidePanel = styled.aside<{ isOpen: boolean }>`
  width: ${props => props.isOpen ? '320px' : '0'};
  background: ${theme.colors.surface};
  border-left: 1px solid ${theme.colors.border};
  transition: width 0.3s ease;
  overflow: hidden;
`;

const App: React.FC = () => {
  const [isPanelOpen, setIsPanelOpen] = React.useState(false);
  const { userProfile, updateUserProfile } = useChat();

  const togglePanel = () => {
    setIsPanelOpen(!isPanelOpen);
  };

  return (
    <ThemeProvider theme={theme}>
      <GlobalStyle />
      <AppContainer>
        <MainContent>
          <Header>
            <Logo>
              <span className="icon">🏦</span>
              <span className="text">Finance Agents</span>
            </Logo>
            <div style={{ display: 'flex', alignItems: 'center', gap: theme.spacing.md }}>
              <SystemStatus>
                <span className="status-indicator" />
                <span>系統正常</span>
              </SystemStatus>
              <button
                onClick={togglePanel}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: theme.spacing.sm,
                  borderRadius: theme.borderRadius.md,
                  color: theme.colors.text.muted,
                  fontSize: '1.1rem',
                }}
                title="用戶設定"
              >
                ⚙️
              </button>
            </div>
          </Header>

          <ChatArea>
            <ChatContainer />
          </ChatArea>
        </MainContent>

        <SidePanel isOpen={isPanelOpen}>
          <UserProfilePanel
            userProfile={userProfile}
            onUpdateProfile={updateUserProfile}
            isOpen={isPanelOpen}
            onClose={() => setIsPanelOpen(false)}
          />
        </SidePanel>
      </AppContainer>

      <ToastContainer
        position="top-right"
        autoClose={3000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="light"
      />
    </ThemeProvider>
  );
};

export default App;