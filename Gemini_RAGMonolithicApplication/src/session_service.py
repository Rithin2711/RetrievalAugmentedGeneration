import os
import json
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import ChatSession, ChatMessage

SESSIONS_DIR = os.getenv("SESSIONS_DIR", "./sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)

class SessionService:
    def __init__(self):
        self.sessions_index_file = os.path.join(SESSIONS_DIR, "sessions_index.json")
    
    def _load_sessions_index(self) -> Dict[str, Any]:
        """Load sessions index from JSON file"""
        if os.path.exists(self.sessions_index_file):
            try:
                with open(self.sessions_index_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def _save_sessions_index(self, index: Dict[str, Any]) -> None:
        """Save sessions index to JSON file"""
        with open(self.sessions_index_file, 'w') as f:
            json.dump(index, f, indent=2, default=str)
    
    def _get_session_file_path(self, session_id: str) -> str:
        """Get file path for a session"""
        return os.path.join(SESSIONS_DIR, f"{session_id}.json")
    
    def _load_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session data from file"""
        session_file = self._get_session_file_path(session_id)
        if os.path.exists(session_file):
            try:
                with open(session_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
        return None
    
    def _save_session_data(self, session_id: str, session_data: Dict[str, Any]) -> None:
        """Save session data to file"""
        session_file = self._get_session_file_path(session_id)
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2, default=str)

    # PUBLIC_INTERFACE
    def create_session(self, user_id: str, title: str = "New Chat", document_ids: List[str] = None) -> ChatSession:
        """Create a new chat session"""
        session_id = str(uuid.uuid4())
        
        session = ChatSession(
            id=session_id,
            title=title,
            user_id=user_id,
            document_ids=document_ids or [],
            messages=[]
        )
        
        # Save session data
        self._save_session_data(session_id, session.dict())
        
        # Update sessions index
        index = self._load_sessions_index()
        index[session_id] = {
            "user_id": user_id,
            "title": title,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "is_active": session.is_active,
            "message_count": 0
        }
        self._save_sessions_index(index)
        
        return session
    
    # PUBLIC_INTERFACE
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a chat session by ID"""
        session_data = self._load_session_data(session_id)
        if session_data:
            return ChatSession(**session_data)
        return None
    
    # PUBLIC_INTERFACE
    def update_session(self, session: ChatSession) -> bool:
        """Update a chat session"""
        try:
            session.updated_at = datetime.utcnow()
            
            # Save session data
            self._save_session_data(session.id, session.dict())
            
            # Update sessions index
            index = self._load_sessions_index()
            if session.id in index:
                index[session.id].update({
                    "title": session.title,
                    "updated_at": session.updated_at,
                    "is_active": session.is_active,
                    "message_count": len(session.messages)
                })
                self._save_sessions_index(index)
            
            return True
        except Exception as e:
            print(f"Error updating session: {e}")
            return False
    
    # PUBLIC_INTERFACE
    def add_message(self, session_id: str, message: ChatMessage) -> bool:
        """Add a message to a session"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.messages.append(message)
        return self.update_session(session)
    
    # PUBLIC_INTERFACE
    def get_user_sessions(self, user_id: str, active_only: bool = True) -> List[ChatSession]:
        """Get all sessions for a user"""
        index = self._load_sessions_index()
        user_sessions = []
        
        for session_id, session_info in index.items():
            if session_info.get("user_id") == user_id:
                if not active_only or session_info.get("is_active", True):
                    session = self.get_session(session_id)
                    if session:
                        user_sessions.append(session)
        
        return sorted(user_sessions, key=lambda x: x.updated_at, reverse=True)
    
    # PUBLIC_INTERFACE
    def delete_session(self, session_id: str) -> bool:
        """Delete a chat session"""
        try:
            # Remove session file
            session_file = self._get_session_file_path(session_id)
            if os.path.exists(session_file):
                os.remove(session_file)
            
            # Remove from sessions index
            index = self._load_sessions_index()
            if session_id in index:
                del index[session_id]
                self._save_sessions_index(index)
            
            return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False
    
    # PUBLIC_INTERFACE
    def deactivate_session(self, session_id: str) -> bool:
        """Deactivate a session (soft delete)"""
        session = self.get_session(session_id)
        if session:
            session.is_active = False
            return self.update_session(session)
        return False
    
    # PUBLIC_INTERFACE
    def update_session_title(self, session_id: str, title: str) -> bool:
        """Update session title"""
        session = self.get_session(session_id)
        if session:
            session.title = title
            return self.update_session(session)
        return False
    
    # PUBLIC_INTERFACE
    def get_session_messages(self, session_id: str, limit: int = None) -> List[ChatMessage]:
        """Get messages for a session"""
        session = self.get_session(session_id)
        if session:
            messages = session.messages
            if limit:
                return messages[-limit:]
            return messages
        return []
    
    # PUBLIC_INTERFACE
    def export_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Export session data for download"""
        session = self.get_session(session_id)
        if session:
            return {
                "session_id": session.id,
                "title": session.title,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "document_ids": session.document_ids,
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                        "metadata": msg.metadata
                    }
                    for msg in session.messages
                ]
            }
        return None

# Global instance
session_service = SessionService()
