import React, { useState, useRef, useEffect } from 'react';
import styled from 'styled-components';
import { chatAPI } from '../services/api';

const ChatContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 600px;
  background: white;
  border: 1px solid #eee;
  border-radius: 12px;
  overflow: hidden;
`;

const MessagesContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #fafafa;
`;

const Message = styled.div`
  margin-bottom: 16px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
`;

const MessageBubble = styled.div`
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.4;
  
  ${props => props.isUser ? `
    background: linear-gradient(90deg, var(--primary-blue) 0%, var(--primary-magenta) 100%);
    color: white;
    margin-left: auto;
    border-bottom-right-radius: 4px;
  ` : `
    background: white;
    border: 1px solid #eee;
    color: #333;
    border-bottom-left-radius: 4px;
  `}
`;

const MessageTime = styled.div`
  font-size: 12px;
  color: #999;
  margin-top: 4px;
`;

const MessageSources = styled.div`
  font-size: 12px;
  margin-top: 8px;
  opacity: 0.8;
`;

const InputContainer = styled.div`
  padding: 16px;
  background: white;
  border-top: 1px solid #eee;
`;

const InputRow = styled.div`
  display: flex;
  gap: 12px;
  align-items: flex-end;
`;

const MessageInput = styled.textarea`
  flex: 1;
  border: 1px solid #ddd;
  border-radius: 20px;
  padding: 12px 16px;
  font-size: 14px;
  resize: none;
  min-height: 20px;
  max-height: 100px;
  font-family: inherit;

  &:focus {
    outline: none;
    border-color: var(--primary-blue);
  }

  &::placeholder {
    color: #999;
  }
`;

const SendButton = styled.button`
  background: linear-gradient(90deg, var(--primary-blue) 0%, var(--primary-magenta) 100%);
  color: white;
  border: none;
  border-radius: 50%;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: opacity 0.2s ease;

  &:hover {
    opacity: 0.9;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const OptionsRow = styled.div`
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  align-items: center;
`;

const Checkbox = styled.input`
  margin-right: 6px;
`;

const CheckboxLabel = styled.label`
  font-size: 14px;
  color: #666;
  cursor: pointer;
  display: flex;
  align-items: center;
`;

const TypingIndicator = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  color: #666;
  font-size: 14px;
`;

const EmptyState = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  text-align: center;
`;

// Simple send icon
const SendIcon = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
    <path d="M2 10L18 2L14 10L18 18L2 10Z" />
  </svg>
);

// PUBLIC_INTERFACE
const ChatInterface = ({ 
  sessionId, 
  documents = [], 
  onNewSession,
  initialMessages = []
}) => {
  const [messages, setMessages] = useState(initialMessages);
  const [inputText, setInputText] = useState('');
  const [useContext, setUseContext] = useState(true);
  const [sending, setSending] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState(sessionId);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    setMessages(initialMessages);
    setCurrentSessionId(sessionId);
  }, [sessionId, initialMessages]);

  const handleSendMessage = async () => {
    if (!inputText.trim() || sending) return;

    const userMessage = inputText.trim();
    setInputText('');
    setSending(true);

    // Add user message to UI immediately
    const newUserMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, newUserMessage]);

    try {
      const documentIds = documents.map(doc => doc.id);
      
      const response = await chatAPI.sendMessage(
        userMessage,
        currentSessionId,
        documentIds,
        useContext
      );

      // Add AI response
      const aiMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.message,
        timestamp: new Date().toISOString(),
        metadata: {
          sources: response.sources,
          confidence: response.confidence
        }
      };

      setMessages(prev => [...prev, aiMessage]);

      // Update session ID if it's a new session
      if (!currentSessionId && response.session_id) {
        setCurrentSessionId(response.session_id);
        if (onNewSession) {
          onNewSession(response.session_id);
        }
      }

    } catch (error) {
      console.error('Failed to send message:', error);
      
      // Add error message
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your message. Please try again.',
        timestamp: new Date().toISOString(),
        isError: true
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const formatSources = (sources) => {
    if (!sources || sources.length === 0) return null;
    
    const sourceDocuments = documents.filter(doc => sources.includes(doc.id));
    if (sourceDocuments.length === 0) return null;
    
    return (
      <MessageSources>
        📚 Sources: {sourceDocuments.map(doc => doc.filename).join(', ')}
      </MessageSources>
    );
  };

  return (
    <ChatContainer>
      <MessagesContainer>
        {messages.length === 0 ? (
          <EmptyState>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>💬</div>
            <div style={{ fontSize: '18px', marginBottom: '8px' }}>Start a conversation</div>
            <div>Ask questions about your documents or chat with the AI assistant</div>
          </EmptyState>
        ) : (
          <>
            {messages.map(message => (
              <Message key={message.id}>
                <MessageBubble isUser={message.role === 'user'} isError={message.isError}>
                  <div>{message.content}</div>
                  <MessageTime>{formatTime(message.timestamp)}</MessageTime>
                  {message.metadata?.sources && formatSources(message.metadata.sources)}
                  {message.metadata?.confidence && (
                    <MessageSources>
                      Confidence: {(message.metadata.confidence * 100).toFixed(0)}%
                    </MessageSources>
                  )}
                </MessageBubble>
              </Message>
            ))}
            {sending && (
              <TypingIndicator>
                <div>AI is thinking...</div>
              </TypingIndicator>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </MessagesContainer>
      
      <InputContainer>
        <OptionsRow>
          <CheckboxLabel>
            <Checkbox
              type="checkbox"
              checked={useContext}
              onChange={(e) => setUseContext(e.target.checked)}
            />
            Use document context
          </CheckboxLabel>
          {documents.length > 0 && (
            <div style={{ fontSize: '14px', color: '#666' }}>
              {documents.length} document{documents.length !== 1 ? 's' : ''} available
            </div>
          )}
        </OptionsRow>
        
        <InputRow>
          <MessageInput
            ref={inputRef}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={documents.length > 0 ? 
              "Ask a question about your documents..." : 
              "Type a message..."
            }
            rows="1"
            disabled={sending}
          />
          <SendButton onClick={handleSendMessage} disabled={!inputText.trim() || sending}>
            <SendIcon />
          </SendButton>
        </InputRow>
      </InputContainer>
    </ChatContainer>
  );
};

export default ChatInterface;
