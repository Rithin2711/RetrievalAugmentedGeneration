import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { useAuth } from '../contexts/AuthContext';
import DocumentUpload from '../components/DocumentUpload';
import DocumentList from '../components/DocumentList';
import ChatInterface from '../components/ChatInterface';
import SessionList from '../components/SessionList';
import { documentsAPI, chatAPI } from '../services/api';

const DashboardContainer = styled.div`
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
  min-height: calc(100vh - 200px);
`;

const WelcomeHeader = styled.div`
  text-align: center;
  margin-bottom: 32px;
`;

const Title = styled.h1`
  color: var(--primary-blue);
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 8px;
`;

const Subtitle = styled.p`
  color: #666;
  font-size: 16px;
  margin: 0;
`;

const MainLayout = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
  margin-bottom: 32px;

  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
`;

const LeftPanel = styled.div`
  display: flex;
  flex-direction: column;
  gap: 24px;
`;

const RightPanel = styled.div`
  display: flex;
  flex-direction: column;
  gap: 24px;
`;

const LoadingSpinner = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #666;
`;

const ErrorMessage = styled.div`
  background: #ffe6e6;
  color: #c62828;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 24px;
  border: 1px solid #ffcdd2;
`;

const StatsBar = styled.div`
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  border: 1px solid #eee;

  @media (max-width: 768px) {
    flex-direction: column;
    gap: 12px;
  }
`;

const StatItem = styled.div`
  text-align: center;
`;

const StatNumber = styled.div`
  font-size: 24px;
  font-weight: 700;
  color: var(--primary-blue);
`;

const StatLabel = styled.div`
  font-size: 14px;
  color: #666;
`;

// PUBLIC_INTERFACE
const DashboardPage = () => {
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [documents, setDocuments] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [currentSession, setCurrentSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!authLoading && !user) {
      navigate('/login');
      return;
    }

    if (user) {
      loadData();
    }
  }, [user, authLoading, navigate]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError('');

      const [documentsData, sessionsData] = await Promise.all([
        documentsAPI.getAll(),
        chatAPI.getSessions()
      ]);

      setDocuments(documentsData);
      setSessions(sessionsData);

      // Set active session to the most recent one
      if (sessionsData.length > 0) {
        const mostRecent = sessionsData[0];
        setActiveSessionId(mostRecent.id);
        setCurrentSession(mostRecent);
      }

    } catch (error) {
      console.error('Failed to load data:', error);
      setError('Failed to load dashboard data. Please refresh the page.');
    } finally {
      setLoading(false);
    }
  };

  const handleUploadSuccess = (newDocument) => {
    setDocuments(prev => [newDocument, ...prev]);
  };

  const handleDocumentDeleted = (documentId) => {
    setDocuments(prev => prev.filter(doc => doc.id !== documentId));
  };

  const handleSessionSelect = async (sessionId) => {
    try {
      const sessionData = await chatAPI.getSession(sessionId);
      setActiveSessionId(sessionId);
      setCurrentSession(sessionData);
    } catch (error) {
      console.error('Failed to load session:', error);
      setError('Failed to load chat session.');
    }
  };

  const handleSessionDeleted = (sessionId) => {
    setSessions(prev => prev.filter(session => session.id !== sessionId));
    
    if (activeSessionId === sessionId) {
      const remainingSessions = sessions.filter(s => s.id !== sessionId);
      if (remainingSessions.length > 0) {
        handleSessionSelect(remainingSessions[0].id);
      } else {
        setActiveSessionId(null);
        setCurrentSession(null);
      }
    }
  };

  const handleNewSession = () => {
    setActiveSessionId(null);
    setCurrentSession(null);
  };

  const handleChatNewSession = (sessionId) => {
    // Refresh sessions to include the new one
    loadData();
    setActiveSessionId(sessionId);
  };

  if (authLoading || loading) {
    return (
      <DashboardContainer>
        <LoadingSpinner>Loading dashboard...</LoadingSpinner>
      </DashboardContainer>
    );
  }

  return (
    <DashboardContainer>
      <WelcomeHeader>
        <Title>Welcome, {user?.username}!</Title>
        <Subtitle>Upload documents and start chatting with your AI assistant</Subtitle>
      </WelcomeHeader>

      {error && <ErrorMessage>{error}</ErrorMessage>}

      <StatsBar>
        <StatItem>
          <StatNumber>{documents.length}</StatNumber>
          <StatLabel>Documents</StatLabel>
        </StatItem>
        <StatItem>
          <StatNumber>{sessions.length}</StatNumber>
          <StatLabel>Chat Sessions</StatLabel>
        </StatItem>
        <StatItem>
          <StatNumber>{documents.reduce((sum, doc) => sum + doc.chunk_count, 0)}</StatNumber>
          <StatLabel>Text Chunks</StatLabel>
        </StatItem>
        <StatItem>
          <StatNumber>{sessions.reduce((sum, session) => sum + (session.messages?.length || 0), 0)}</StatNumber>
          <StatLabel>Messages</StatLabel>
        </StatItem>
      </StatsBar>

      <MainLayout>
        <LeftPanel>
          <DocumentUpload onUploadSuccess={handleUploadSuccess} />
          <DocumentList
            documents={documents}
            onDocumentDeleted={handleDocumentDeleted}
            loading={false}
          />
        </LeftPanel>

        <RightPanel>
          <SessionList
            sessions={sessions}
            activeSessionId={activeSessionId}
            onSessionSelect={handleSessionSelect}
            onSessionDeleted={handleSessionDeleted}
            onNewSession={handleNewSession}
            loading={false}
          />
          <ChatInterface
            sessionId={activeSessionId}
            documents={documents}
            onNewSession={handleChatNewSession}
            initialMessages={currentSession?.messages || []}
          />
        </RightPanel>
      </MainLayout>
    </DashboardContainer>
  );
};

export default DashboardPage;
