import React, { useState } from 'react';
import styled from 'styled-components';
import { documentsAPI } from '../services/api';

const ListContainer = styled.div`
  margin-bottom: 24px;
`;

const ListHeader = styled.h3`
  color: var(--primary-blue);
  margin-bottom: 16px;
  font-size: 18px;
  font-weight: 600;
`;

const DocumentItem = styled.div`
  background: white;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: border-color 0.2s ease;

  &:hover {
    border-color: var(--primary-blue);
  }
`;

const DocumentInfo = styled.div`
  flex: 1;
`;

const DocumentName = styled.div`
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
`;

const DocumentMeta = styled.div`
  font-size: 14px;
  color: #666;
  display: flex;
  gap: 16px;
`;

const DocumentActions = styled.div`
  display: flex;
  gap: 8px;
`;

const ActionButton = styled.button`
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
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

const DeleteButton = styled(ActionButton)`
  background: #e74c3c;
  color: white;
`;

const StatusBadge = styled.span`
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  background: ${props => props.processed ? '#27ae60' : '#f39c12'};
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
const DocumentList = ({ documents, onDocumentDeleted, loading }) => {
  const [deleting, setDeleting] = useState(new Set());

  const handleDelete = async (documentId, documentName) => {
    if (!window.confirm(`Are you sure you want to delete "${documentName}"?`)) {
      return;
    }

    setDeleting(prev => new Set([...prev, documentId]));

    try {
      await documentsAPI.delete(documentId);
      
      if (onDocumentDeleted) {
        onDocumentDeleted(documentId);
      }
    } catch (error) {
      alert('Failed to delete document: ' + (error.response?.data?.detail || error.message));
    } finally {
      setDeleting(prev => {
        const newSet = new Set(prev);
        newSet.delete(documentId);
        return newSet;
      });
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <ListContainer>
        <ListHeader>Your Documents</ListHeader>
        <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
          Loading documents...
        </div>
      </ListContainer>
    );
  }

  if (!documents || documents.length === 0) {
    return (
      <ListContainer>
        <ListHeader>Your Documents</ListHeader>
        <EmptyState>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>📄</div>
          <div style={{ fontSize: '18px', marginBottom: '8px' }}>No documents uploaded yet</div>
          <div>Upload your first document to get started with AI chat</div>
        </EmptyState>
      </ListContainer>
    );
  }

  return (
    <ListContainer>
      <ListHeader>Your Documents ({documents.length})</ListHeader>
      {documents.map(doc => (
        <DocumentItem key={doc.id}>
          <DocumentInfo>
            <DocumentName>{doc.filename}</DocumentName>
            <DocumentMeta>
              <span>{formatFileSize(doc.size)}</span>
              <span>{formatDate(doc.upload_date)}</span>
              <StatusBadge processed={doc.processed}>
                {doc.processed ? 'Processed' : 'Processing'}
              </StatusBadge>
              {doc.chunk_count > 0 && (
                <span>{doc.chunk_count} chunks</span>
              )}
            </DocumentMeta>
          </DocumentInfo>
          <DocumentActions>
            <DeleteButton
              onClick={() => handleDelete(doc.id, doc.filename)}
              disabled={deleting.has(doc.id)}
            >
              {deleting.has(doc.id) ? 'Deleting...' : 'Delete'}
            </DeleteButton>
          </DocumentActions>
        </DocumentItem>
      ))}
    </ListContainer>
  );
};

export default DocumentList;
