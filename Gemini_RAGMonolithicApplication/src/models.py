from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    """Document types supported by the system"""
    PDF = "pdf"
    TEXT = "txt"
    JSON = "json"

class UserRole(str, Enum):
    """User roles in the system"""
    ADMIN = "admin"
    USER = "user"

# PUBLIC_INTERFACE
class User(BaseModel):
    """User model for authentication and authorization"""
    id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Username for authentication")
    email: str = Field(..., description="User email address")
    role: UserRole = Field(default=UserRole.USER, description="User role")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    is_active: bool = Field(default=True, description="Whether user account is active")

# PUBLIC_INTERFACE
class UserCreate(BaseModel):
    """Model for creating new users"""
    username: str = Field(..., min_length=3, max_length=50, description="Username (3-50 characters)")
    email: str = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")
    role: UserRole = Field(default=UserRole.USER, description="User role")

# PUBLIC_INTERFACE
class UserLogin(BaseModel):
    """Model for user login credentials"""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")

# PUBLIC_INTERFACE
class Token(BaseModel):
    """JWT token response model"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")

# PUBLIC_INTERFACE
class Document(BaseModel):
    """Document model for uploaded files"""
    id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type of the document")
    size: int = Field(..., description="File size in bytes")
    document_type: DocumentType = Field(..., description="Type of document")
    upload_date: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")
    user_id: str = Field(..., description="ID of user who uploaded the document")
    processed: bool = Field(default=False, description="Whether document has been processed for embeddings")
    chunk_count: int = Field(default=0, description="Number of text chunks created")

# PUBLIC_INTERFACE
class DocumentUpload(BaseModel):
    """Model for document upload requests"""
    filename: str = Field(..., description="Document filename")
    content_type: str = Field(..., description="Document MIME type")

# PUBLIC_INTERFACE
class ChatMessage(BaseModel):
    """Individual chat message model"""
    id: str = Field(..., description="Unique message identifier")
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional message metadata")

# PUBLIC_INTERFACE
class ChatSession(BaseModel):
    """Chat session model containing conversation history"""
    id: str = Field(..., description="Unique session identifier")
    title: str = Field(..., description="Session title/summary")
    user_id: str = Field(..., description="ID of user who owns the session")
    document_ids: List[str] = Field(default=[], description="List of document IDs associated with session")
    messages: List[ChatMessage] = Field(default=[], description="List of messages in the session")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Session creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    is_active: bool = Field(default=True, description="Whether session is active")

# PUBLIC_INTERFACE
class ChatRequest(BaseModel):
    """Model for chat message requests"""
    message: str = Field(..., min_length=1, max_length=4000, description="User message content")
    session_id: Optional[str] = Field(default=None, description="Existing session ID (optional)")
    document_ids: Optional[List[str]] = Field(default=None, description="Document IDs to reference")
    use_context: bool = Field(default=True, description="Whether to use document context")

# PUBLIC_INTERFACE
class ChatResponse(BaseModel):
    """Model for chat response"""
    message: str = Field(..., description="Assistant response")
    session_id: str = Field(..., description="Session ID for the conversation")
    sources: Optional[List[str]] = Field(default=None, description="Document sources used in response")
    confidence: Optional[float] = Field(default=None, description="Confidence score for the response")

# PUBLIC_INTERFACE
class SessionExport(BaseModel):
    """Model for session export requests"""
    format: str = Field(..., description="Export format (json or pdf)")
    include_metadata: bool = Field(default=True, description="Whether to include metadata")

# PUBLIC_INTERFACE
class DocumentChunk(BaseModel):
    """Model for document text chunks used in embeddings"""
    id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Parent document identifier")
    content: str = Field(..., description="Chunk text content")
    chunk_index: int = Field(..., description="Index of chunk within document")
    start_char: int = Field(..., description="Starting character position in original document")
    end_char: int = Field(..., description="Ending character position in original document")
    embedding: Optional[List[float]] = Field(default=None, description="Vector embedding for the chunk")

# PUBLIC_INTERFACE
class SearchResult(BaseModel):
    """Model for document search results"""
    chunk_id: str = Field(..., description="Matching chunk identifier")
    document_id: str = Field(..., description="Source document identifier")
    content: str = Field(..., description="Matching text content")
    score: float = Field(..., description="Relevance score")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

# PUBLIC_INTERFACE
class HealthStatus(BaseModel):
    """Model for health check responses"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    version: str = Field(..., description="Application version")
    uptime: Optional[float] = Field(default=None, description="Service uptime in seconds")
