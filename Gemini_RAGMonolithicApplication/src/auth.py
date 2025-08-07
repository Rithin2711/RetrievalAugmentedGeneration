import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends
import uuid

from .models import User, UserCreate

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# Security scheme
security = HTTPBearer()

# In-memory user storage (replace with database in production)
USERS_FILE = os.path.join(os.path.dirname(__file__), "..", "users.json")

def _load_users() -> Dict[str, Any]:
    """Load users from JSON file"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def _save_users(users: Dict[str, Any]) -> None:
    """Save users to JSON file"""
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2, default=str)

# PUBLIC_INTERFACE
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

# PUBLIC_INTERFACE
def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)

# PUBLIC_INTERFACE
def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate user with username/email and password"""
    users = _load_users()
    
    # Find user by username or email
    user_data = None
    for uid, data in users.items():
        if data.get("username") == username or data.get("email") == username:
            user_data = data
            break
    
    if not user_data or not verify_password(password, user_data["hashed_password"]):
        return None
    
    return User(**{k: v for k, v in user_data.items() if k != "hashed_password"})

# PUBLIC_INTERFACE
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# PUBLIC_INTERFACE
def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# PUBLIC_INTERFACE
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    payload = verify_token(token)
    
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    
    users = _load_users()
    user_data = None
    for uid, data in users.items():
        if data.get("username") == username:
            user_data = data
            break
    
    if user_data is None or not user_data.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    return User(**{k: v for k, v in user_data.items() if k != "hashed_password"})

# PUBLIC_INTERFACE
def create_user(user_create: UserCreate) -> User:
    """Create a new user"""
    users = _load_users()
    
    # Check if username or email already exists
    for data in users.values():
        if data.get("username") == user_create.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        if data.get("email") == user_create.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Create new user
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user_create.password)
    
    user_data = {
        "id": user_id,
        "username": user_create.username,
        "email": user_create.email,
        "role": user_create.role,
        "created_at": datetime.utcnow(),
        "is_active": True,
        "hashed_password": hashed_password
    }
    
    users[user_id] = user_data
    _save_users(users)
    
    return User(**{k: v for k, v in user_data.items() if k != "hashed_password"})

# PUBLIC_INTERFACE  
def get_user_by_id(user_id: str) -> Optional[User]:
    """Get user by ID"""
    users = _load_users()
    user_data = users.get(user_id)
    
    if not user_data:
        return None
    
    return User(**{k: v for k, v in user_data.items() if k != "hashed_password"})
