import React, { useState } from 'react';
import styled from 'styled-components';
import { chatAPI } from '../services/api';

const ListContainer = styled.div`
  margin-bottom: 24px;
`;

const ListHeader = styled.div`
  display: flex;
  justify-content: between;
  align-items: center;
  margin-bottom: 16px;
`;

const Title = styled.h3`
  color: var(--primary-blue);
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  flex: 1;
`;

const NewChatButton = styled.button`
  background: linear-gradient(90deg, var(--primary-blue) 0%, var(--primary-magenta) 100%);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s ease;

  &:hover {
    opacity: 0.9;
  }
`;

const SessionItem = styled.div`
  background: white;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  justify-content: space-between;
  align-items: center;

  &:hover {
    border-color: var(--primary-blue);
    box-shadow: 0 2px 8px rgba(36, 54, 168, 0.1);
  }

  ${props => props.active && `
    border-color: var(--primary-blue);
    background: rgba(36, 54, 168, 0.05);
  `}
`;

const SessionInfo = styled.div`
  flex: 1;
  min-width: 0;
`;

const SessionTitle = styled.div`
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;

const SessionMeta = styled.div`
  font-size: 14px;
  color: #666;
  display: flex;
  gap: 16px;
`;

const SessionActions = styled.div`
  display: flex;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.2s ease;

  ${SessionItem}:hover & {
    opacity: 1;
  }
`;

const ActionButton = styled.button`
  padding: 4px 8px;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: opacity 0.2s ease;

  &:hover {
    opacity: 0.8;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const ExportButton = styled(ActionButton)`
  background: var(--accent-yellow);
  color: #333;
`;

const DeleteButton = styled(ActionButton)`
  background: #e74c3c;
  color: white;
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 40px;
  color: #999;
  background: #f9f9f9;
  border-radius: 8px;
`;

// PUBLIC_INTERFACE
const SessionList = ({ 
  sessions, 
  activeSessionId, 
  onSessionSelect, 
  onSessionDeleted,
  onNewSession,
  loading 
}) => {
  const [deleting, setDeleting] = useState(new Set());
  const [exporting, setExporting] = useState(new Set());

  const handleSessionClick = (sessionId) => {
    if (onSessionSelect) {
      onSessionSelect(sessionId);
    }
  };

  const handleDelete = async (e, sessionId, sessionTitle) => {
    e.stopPropagation();
    
    if (!window.confirm(`Are you sure you want to delete "${sessionTitle}"?`)) {
      return;
    }

    setDeleting(prev => new Set([...prev, sessionId]));

    try {
      await chatAPI.deleteSession(sessionId);
      
      if (onSessionDeleted) {
        onSessionDeleted(sessionId);
      }
    } catch (error) {
      alert('Failed to delete session: ' + (error.response?.data?.detail || error.message));
    } finally {
      setDeleting(prev => {
        const newSet = new Set(prev);
        newSet.delete(sessionId);
        return newSet;
      });
    }
  };

  const handleExport = async (e, sessionId, sessionTitle) => {
    e.stopPropagation();
    
    setExporting(prev => new Set([...prev, sessionId]));

    try {
      const blob = await chatAPI.exportSession(sessionId, 'json');
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `chat_session_${sessionTitle}_${sessionId.slice(0, 8)}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
    } catch (error) {
      alert('Failed to export session: ' + (error.response?.data?.detail || error.message));
    } finally {
      setExporting(prev => {
        const newSet = new Set(prev);
        newSet.delete(sessionId);
        return newSet;
      });
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now - date) / (1000 * 60 * 60);
    
    if (diffInHours < 24) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffInHours < 24 * 7) {
      return date.toLocaleDateString([], { weekday: 'short' });
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  };

  if (loading) {
    return (
      <ListContainer>
        <ListHeader>
          <Title>Chat Sessions</Title>
        </ListHeader>
        <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
          Loading sessions...
        </div>
      </ListContainer>
    );
  }

  return (
    <ListContainer>
      <ListHeader>
        <Title>Chat Sessions</Title>
        {onNewSession && (
          <NewChatButton onClick={onNewSession}>
            New Chat
          </NewChatButton>
        )}
      </ListHeader>
      
      {!sessions || sessions.length === 0 ? (
        <EmptyState>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>💬</div>
          <div style={{ fontSize: '18px', marginBottom: '8px' }}>No chat sessions yet</div>
          <div>Start a new conversation to begin chatting with AI</div>
        </EmptyState>
      ) : (
        sessions.map(session => (
          <SessionItem
            key={session.id}
            active={session.id === activeSessionId}
            onClick={() => handleSessionClick(session.id)}
          >
            <SessionInfo>
              <SessionTitle>{session.title}</SessionTitle>
              <SessionMeta>
                <span>{session.messages?.length || 0} messages</span>
                <span>{formatDate(session.updated_at)}</span>
              </SessionMeta>
            </SessionInfo>
            <SessionActions>
              <ExportButton
                onClick={(e) => handleExport(e, session.id, session.title)}
                disabled={exporting.has(session.id)}
                title="Export session"
              >
                {exporting.has(session.id) ? '...' : '📥'}
              </ExportButton>
              <DeleteButton
                onClick={(e) => handleDelete(e, session.id, session.title)}
                disabled={deleting.has(session.id)}
                title="Delete session"
              >
                {deleting.has(session.id) ? '...' : '🗑️'}
              </DeleteButton>
            </SessionActions>
          </SessionItem>
        ))
      )}
    </ListContainer>
  );
};

export default SessionList;
