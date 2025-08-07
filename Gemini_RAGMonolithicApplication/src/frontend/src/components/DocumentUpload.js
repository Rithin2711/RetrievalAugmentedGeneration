import React, { useState, useRef } from 'react';
import styled from 'styled-components';
import { documentsAPI } from '../services/api';

const UploadContainer = styled.div`
  margin-bottom: 24px;
`;

const DropZone = styled.div`
  border: 2px dashed ${props => props.isDragging ? 'var(--primary-blue)' : '#ddd'};
  border-radius: 8px;
  padding: 32px;
  text-align: center;
  background: ${props => props.isDragging ? 'rgba(36, 54, 168, 0.05)' : '#fafafa'};
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    border-color: var(--primary-blue);
    background: rgba(36, 54, 168, 0.05);
  }
`;

const UploadText = styled.div`
  font-size: 16px;
  color: #666;
  margin-bottom: 8px;
`;

const FileInput = styled.input`
  display: none;
`;

const UploadButton = styled.button`
  background: linear-gradient(90deg, var(--primary-blue) 0%, var(--primary-magenta) 100%);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s ease;

  &:hover {
    opacity: 0.9;
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const ProgressBar = styled.div`
  width: 100%;
  height: 8px;
  background: #eee;
  border-radius: 4px;
  margin-top: 16px;
  overflow: hidden;
`;

const Progress = styled.div`
  width: ${props => props.progress}%;
  height: 100%;
  background: linear-gradient(90deg, var(--primary-blue) 0%, var(--primary-magenta) 100%);
  transition: width 0.3s ease;
`;

const ErrorMessage = styled.div`
  color: #e74c3c;
  font-size: 14px;
  margin-top: 8px;
`;

const SuccessMessage = styled.div`
  color: #27ae60;
  font-size: 14px;
  margin-top: 8px;
`;

// PUBLIC_INTERFACE
const DocumentUpload = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const fileInputRef = useRef(null);

  const handleDragEnter = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    if (e.currentTarget.contains(e.relatedTarget)) return;
    setIsDragging(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileUpload = async (file) => {
    // Validate file type
    const allowedTypes = ['application/pdf', 'text/plain', 'application/json'];
    const allowedExtensions = ['.pdf', '.txt', '.json'];
    
    const isValidType = allowedTypes.includes(file.type) || 
                       allowedExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
    
    if (!isValidType) {
      setError('Please upload a PDF, TXT, or JSON file.');
      return;
    }

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB.');
      return;
    }

    setUploading(true);
    setProgress(0);
    setError('');
    setSuccess('');

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90));
      }, 100);

      const result = await documentsAPI.upload(file);
      
      clearInterval(progressInterval);
      setProgress(100);
      
      setSuccess(`Successfully uploaded "${file.name}"`);
      
      if (onUploadSuccess) {
        onUploadSuccess(result);
      }
      
      // Reset form
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
      setTimeout(() => {
        setProgress(0);
        setSuccess('');
      }, 3000);

    } catch (error) {
      setError(error.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <UploadContainer>
      <DropZone
        isDragging={isDragging}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <UploadText>
          {uploading ? 'Uploading...' : 'Drag & drop files here or click to browse'}
        </UploadText>
        <div style={{ fontSize: '14px', color: '#999', marginBottom: '16px' }}>
          Supported formats: PDF, TXT, JSON (max 10MB)
        </div>
        <UploadButton disabled={uploading}>
          {uploading ? 'Processing...' : 'Choose Files'}
        </UploadButton>
        
        <FileInput
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt,.json,application/pdf,text/plain,application/json"
          onChange={handleFileSelect}
        />
        
        {uploading && (
          <ProgressBar>
            <Progress progress={progress} />
          </ProgressBar>
        )}
      </DropZone>
      
      {error && <ErrorMessage>{error}</ErrorMessage>}
      {success && <SuccessMessage>{success}</SuccessMessage>}
    </UploadContainer>
  );
};

export default DocumentUpload;
