from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware, Request, HTTPException, Depends, UploadFile, File, status
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timedelta
import os
import json
import uuid
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from ..models import (
    User, UserCreate, UserLogin, Token, Document, ChatRequest, ChatResponse,
    ChatSession, ChatMessage, SearchResult, HealthStatus
)
from ..auth import authenticate_user, create_access_token, get_current_user, create_user
from ..document_service import document_service
from ..embedding_service import embedding_service
from ..gemini_service import gemini_service
from ..session_service import session_service

# Create FastAPI app with metadata
app = FastAPI(
    title="Gemini RAG Chat API",
    description="Retrieval-Augmented Generation chat system using Google Gemini API",
    version="1.0.0",
    openapi_tags=[
        {"name": "auth", "description": "Authentication and user management"},
        {"name": "documents", "description": "Document upload and management"},
        {"name": "chat", "description": "Chat sessions and messaging"},
        {"name": "export", "description": "Session export functionality"},
        {"name": "health", "description": "Health checks and system status"},
    ]
)

# CORS middleware
# Always include the deployed frontend in allowed origins
required_frontend_origin = "https://vscode-internal-17605-beta.beta01.cloud.kavia.ai:3000"
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
if required_frontend_origin not in allowed_origins:
    allowed_origins.append(required_frontend_origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the built frontend
static_path = os.path.join(os.path.dirname(__file__), '..', 'static')
app.mount("/static", StaticFiles(directory=static_path), name="static")

# ========== HEALTH ENDPOINTS ==========

@app.get("/api/health", response_model=HealthStatus, tags=["health"])
def health_check():
    """PUBLIC_INTERFACE
    Health check endpoint that returns system status and basic information.
    
    Returns:
        HealthStatus: Current system health status
    """
    return HealthStatus(
        status="healthy",
        version="1.0.0",
        uptime=None
    )

# ========== AUTHENTICATION ENDPOINTS ==========

@app.options("/api/auth/register", tags=["auth"])
def options_register():
    """PUBLIC_INTERFACE
    Handle CORS preflight OPTIONS request for user registration.
    Returns 200 and allows browser to proceed with POST.
    """
    return {}  # FastAPI with CORSMiddleware will add the appropriate headers

@app.post("/api/auth/register", response_model=User, tags=["auth"])
def register_user(user_data: UserCreate):
    """PUBLIC_INTERFACE
    Register a new user account.
    
    Args:
        user_data: User registration information including username, email, and password
        
    Returns:
        User: Created user information (without password)
        
    Raises:
        HTTPException: If username/email already exists or validation fails
    """
    return create_user(user_data)

@app.post("/api/auth/login", response_model=Token, tags=["auth"])
def login_user(credentials: UserLogin):
    """PUBLIC_INTERFACE
    Authenticate user and return access token.
    
    Args:
        credentials: Username/email and password for authentication
        
    Returns:
        Token: JWT access token and token information
        
    Raises:
        HTTPException: If credentials are invalid
    """
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")))
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        expires_in=int(access_token_expires.total_seconds())
    )

@app.get("/api/auth/me", response_model=User, tags=["auth"])
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """PUBLIC_INTERFACE
    Get current authenticated user information.
    
    Returns:
        User: Current user information
    """
    return current_user

# ========== DOCUMENT ENDPOINTS ==========

@app.post("/api/documents/upload", response_model=Document, tags=["documents"])
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """PUBLIC_INTERFACE
    Upload a document for processing and embedding.
    
    Args:
        file: Document file to upload (PDF, TXT, or JSON)
        current_user: Authenticated user uploading the document
        
    Returns:
        Document: Document metadata and processing status
        
    Raises:
        HTTPException: If file type is unsupported or processing fails
    """
    # Validate file type
    allowed_types = ["application/pdf", "text/plain", "application/json"]
    if file.content_type not in allowed_types and not any(
        file.filename.lower().endswith(ext) for ext in ['.pdf', '.txt', '.json']
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Please upload PDF, TXT, or JSON files."
        )
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Upload document
        document = document_service.upload_document(
            filename=file.filename,
            content_type=file.content_type,
            file_data=file_content,
            user_id=current_user.id
        )
        
        # Process document in background (extract text and create chunks)
        document_service.process_document(document.id)
        
        # Get chunks and add to embedding index
        chunks = document_service.get_document_chunks(document.id)
        embedding_service.batch_add_chunks(chunks)
        
        return document
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )

@app.get("/api/documents", response_model=List[Document], tags=["documents"])
def get_user_documents(current_user: User = Depends(get_current_user)):
    """PUBLIC_INTERFACE
    Get all documents uploaded by the current user.
    
    Returns:
        List[Document]: List of user's documents
    """
    return document_service.get_user_documents(current_user.id)

@app.get("/api/documents/{document_id}", response_model=Document, tags=["documents"])
def get_document(document_id: str, current_user: User = Depends(get_current_user)):
    """PUBLIC_INTERFACE
    Get a specific document by ID.
    
    Args:
        document_id: Unique document identifier
        current_user: Authenticated user requesting the document
        
    Returns:
        Document: Document information
        
    Raises:
        HTTPException: If document not found or access denied
    """
    document = document_service.get_document(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return document

@app.delete("/api/documents/{document_id}", tags=["documents"])
def delete_document(document_id: str, current_user: User = Depends(get_current_user)):
    """PUBLIC_INTERFACE
    Delete a document and its associated embeddings.
    
    Args:
        document_id: Unique document identifier
        current_user: Authenticated user requesting deletion
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If document not found or access denied
    """
    document = document_service.get_document(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get chunks to remove from embeddings
    chunks = document_service.get_document_chunks(document_id)
    chunk_ids = [chunk.id for chunk in chunks]
    
    # Remove from embeddings
    if chunk_ids:
        embedding_service.remove_chunk_embeddings(chunk_ids)
    
    # Delete document
    success = document_service.delete_document(document_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )
    
    return {"message": "Document deleted successfully"}

# ========== CHAT ENDPOINTS ==========

@app.post("/api/chat", response_model=ChatResponse, tags=["chat"])
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """PUBLIC_INTERFACE
    Send a chat message and get AI response with document context.
    
    Args:
        request: Chat request containing message and optional session/document context
        current_user: Authenticated user sending the message
        
    Returns:
        ChatResponse: AI response with session information
    """
    try:
        # Get or create session
        if request.session_id:
            session = session_service.get_session(request.session_id)
            if not session or session.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found"
                )
        else:
            # Create new session
            session = session_service.create_session(
                user_id=current_user.id,
                title="New Chat",
                document_ids=request.document_ids or []
            )
        
        # Search for relevant context if use_context is True
        search_results = []
        if request.use_context:
            # Search embeddings for relevant chunks
            similar_chunks = embedding_service.search_similar_chunks(
                request.message, k=5, threshold=0.3
            )
            
            # Get chunk details
            for chunk_id, score in similar_chunks:
                chunks = document_service._load_chunks()
                chunk_data = chunks.get(chunk_id)
                if chunk_data:
                    search_results.append(SearchResult(
                        chunk_id=chunk_id,
                        document_id=chunk_data["document_id"],
                        content=chunk_data["content"],
                        score=score
                    ))
        
        # Add user message to session
        user_message = ChatMessage(
            id=str(uuid.uuid4()),
            role="user",
            content=request.message,
            timestamp=datetime.utcnow()
        )
        session_service.add_message(session.id, user_message)
        
        # Generate AI response
        conversation_history = session.messages[-10:]  # Last 10 messages for context
        ai_response = gemini_service.generate_response(
            user_message=request.message,
            context=search_results,
            conversation_history=conversation_history
        )
        
        # Add AI message to session
        ai_message = ChatMessage(
            id=str(uuid.uuid4()),
            role="assistant",
            content=ai_response,
            timestamp=datetime.utcnow(),
            metadata={"sources": [r.document_id for r in search_results]} if search_results else None
        )
        session_service.add_message(session.id, ai_message)
        
        # Generate session title if this is the first exchange
        if len(session.messages) == 2:  # User message + AI response
            title = gemini_service.generate_session_title(request.message, ai_response)
            session_service.update_session_title(session.id, title)
        
        return ChatResponse(
            message=ai_response,
            session_id=session.id,
            sources=[r.document_id for r in search_results] if search_results else None,
            confidence=max([r.score for r in search_results]) if search_results else None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}"
        )

@app.get("/api/sessions", response_model=List[ChatSession], tags=["chat"])
def get_user_sessions(current_user: User = Depends(get_current_user)):
    """PUBLIC_INTERFACE
    Get all chat sessions for the current user.
    
    Returns:
        List[ChatSession]: List of user's chat sessions
    """
    return session_service.get_user_sessions(current_user.id)

@app.get("/api/sessions/{session_id}", response_model=ChatSession, tags=["chat"])
def get_session(session_id: str, current_user: User = Depends(get_current_user)):
    """PUBLIC_INTERFACE
    Get a specific chat session by ID.
    
    Args:
        session_id: Unique session identifier
        current_user: Authenticated user requesting the session
        
    Returns:
        ChatSession: Session information with messages
        
    Raises:
        HTTPException: If session not found or access denied
    """
    session = session_service.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return session

@app.delete("/api/sessions/{session_id}", tags=["chat"])
def delete_session(session_id: str, current_user: User = Depends(get_current_user)):
    """PUBLIC_INTERFACE
    Delete a chat session.
    
    Args:
        session_id: Unique session identifier
        current_user: Authenticated user requesting deletion
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If session not found or access denied
    """
    session = session_service.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    success = session_service.delete_session(session_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session"
        )
    
    return {"message": "Session deleted successfully"}

# ========== EXPORT ENDPOINTS ==========

@app.get("/api/sessions/{session_id}/export", tags=["export"])
def export_session(
    session_id: str,
    format: str = "json",
    current_user: User = Depends(get_current_user)
):
    """PUBLIC_INTERFACE
    Export a chat session in JSON or PDF format.
    
    Args:
        session_id: Unique session identifier
        format: Export format ("json" or "pdf")
        current_user: Authenticated user requesting export
        
    Returns:
        FileResponse: Downloadable file with session data
        
    Raises:
        HTTPException: If session not found, access denied, or unsupported format
    """
    session = session_service.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if format.lower() not in ["json", "pdf"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported format. Use 'json' or 'pdf'"
        )
    
    # Export session data
    export_data = session_service.export_session(session_id)
    
    if format.lower() == "json":
        # Create temporary JSON file
        temp_file = f"/tmp/session_{session_id}.json"
        with open(temp_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return FileResponse(
            temp_file,
            media_type="application/json",
            filename=f"chat_session_{session.title}_{session_id[:8]}.json"
        )
    
    # PDF format would require additional PDF generation logic
    # For now, return JSON format
    temp_file = f"/tmp/session_{session_id}.json"
    with open(temp_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    return FileResponse(
        temp_file,
        media_type="application/json",
        filename=f"chat_session_{session.title}_{session_id[:8]}.json"
    )

# ========== FRONTEND SERVING ==========

@app.get("/", response_class=HTMLResponse)
async def serve_react_index(request: Request):
    """PUBLIC_INTERFACE
    Serve the React frontend index.html for the root route.
    """
    index_path = os.path.join(static_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return HTMLResponse(
        "<h1>Gemini-RAG Frontend not yet built.<br/>Please run 'npm run build' in /src/frontend.</h1>", 
        status_code=503
    )

# Catch-all for client-side routing (React Router)
@app.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_react_app_catchall(full_path: str):
    """PUBLIC_INTERFACE
    Handle all other routes for React client-side navigation.
    """
    # Don't serve index.html for API routes
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    index_path = os.path.join(static_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return HTMLResponse(
        "<h1>Gemini-RAG Frontend not yet built.<br/>Please run 'npm run build' in /src/frontend.</h1>", 
        status_code=503
    )
