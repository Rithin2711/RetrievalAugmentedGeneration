import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends
import uuid

from .models import User, UserCreate

# Use file_database.py JSON CRUD
from .file_database import add_user, get_user, list_users

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# Security scheme
security = HTTPBearer()

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
    """
    Authenticate user with username/email and password, using persistent JSON store.
    """
    # Try finding by username or by email
    users = list_users()
    user_data = None
    for u in users:
        if (u.get("username") == username or u.get("email") == username):
            user_data = u
            break

    if not user_data or not verify_password(password, user_data["password_hash"]):
        return None

    # sanitize out the password_hash in returned User
    filtered = {k: v for k, v in user_data.items() if k != "password_hash"}
    return User(**filtered)

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

    user_data = get_user(username)

    if user_data is None or not user_data.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    filtered = {k: v for k, v in user_data.items() if k != "password_hash"}
    return User(**filtered)

# PUBLIC_INTERFACE
def create_user(user_create: UserCreate) -> User:
    """Create a new user and store in persistent file-based database"""
    # Check if username or email already exists
    all_users = list_users()
    for u in all_users:
        if u.get("username") == user_create.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        if u.get("email") == user_create.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    user_id = str(uuid.uuid4())
    password_hash = get_password_hash(user_create.password)
    user_data = {
        "id": user_id,
        "username": user_create.username,
        "email": user_create.email,
        "role": user_create.role,
        "created_at": datetime.utcnow().isoformat(),
        "is_active": True,
        "password_hash": password_hash
    }
    if not add_user(user_data):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    filtered = {k: v for k, v in user_data.items() if k != "password_hash"}
    return User(**filtered)

# PUBLIC_INTERFACE
def get_user_by_id(user_id: str) -> Optional[User]:
    """Get user by ID (if username is UUID, but fallback to all users scan)"""
    all_users = list_users()
    for u in all_users:
        if u.get("id") == user_id:
            filtered = {k: v for k, v in u.items() if k != "password_hash"}
            return User(**filtered)
    return None
