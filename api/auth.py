"""
Authentication routes for CollectorStream API
JWT-based authentication with bcrypt password hashing
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, timedelta
import jwt
import bcrypt
import secrets
import os

from database import (
    create_user, get_user_by_email, get_user_by_username, get_user_by_id,
    update_user_password, set_reset_token, get_user_by_reset_token
)

router = APIRouter()
security = HTTPBearer()

# JWT Configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "your-super-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 1 week

# ============================================================================
# Pydantic Models
# ============================================================================

class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

class PasswordResetConfirm(BaseModel):
    new_password: str = Field(..., min_length=8)

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    created_at: Optional[str] = None

class AuthResponse(BaseModel):
    token: str
    user: UserResponse

# ============================================================================
# Helper Functions
# ============================================================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str) -> str:
    """Create a JWT token for a user."""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    """Decode a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get the current user from the JWT token."""
    token = credentials.credentials
    payload = decode_token(token)
    user_id = payload.get("user_id")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not user.get("is_active"):
        raise HTTPException(status_code=401, detail="User is inactive")

    return user

def format_user(user: dict) -> dict:
    """Format user for response."""
    return {
        "id": user["id"],
        "email": user["email"],
        "username": user["username"],
        "createdAt": user.get("created_at")
    }

# ============================================================================
# Routes
# ============================================================================

@router.post("/register", response_model=AuthResponse)
async def register(data: UserRegister):
    """Register a new user."""
    # Check if email exists
    if get_user_by_email(data.email):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Email already registered"
        )

    # Check if username exists
    if get_user_by_username(data.username):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username already taken"
        )

    # Create user
    password_hash = hash_password(data.password)
    user = create_user(data.email, data.username, password_hash)

    # Generate token
    token = create_token(user["id"])

    return {
        "token": token,
        "user": format_user(user)
    }

@router.post("/login", response_model=AuthResponse)
async def login(data: UserLogin):
    """Login a user."""
    user = get_user_by_email(data.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not verify_password(data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive"
        )

    token = create_token(user["id"])

    return {
        "token": token,
        "user": format_user(user)
    }

@router.get("/validate", response_model=UserResponse)
async def validate_token(current_user: dict = Depends(get_current_user)):
    """Validate a token and return user info."""
    return format_user(current_user)

@router.post("/reset-password")
async def request_password_reset(data: PasswordReset):
    """Request a password reset email."""
    user = get_user_by_email(data.email)

    # Always return success to prevent email enumeration
    if not user:
        return {"message": "If an account exists, a reset email has been sent"}

    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    expires = (datetime.utcnow() + timedelta(hours=1)).isoformat()

    set_reset_token(user["id"], reset_token, expires)

    # TODO: Send email with reset link
    # For now, just log it (in production, use a proper email service)
    print(f"Password reset requested for {data.email}. Token: {reset_token}")

    return {"message": "If an account exists, a reset email has been sent"}

@router.post("/change-password")
async def change_password(data: PasswordChange, current_user: dict = Depends(get_current_user)):
    """Change the current user's password."""
    # Verify current password
    if not verify_password(data.current_password, current_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Current password is incorrect"
        )

    # Update password
    new_hash = hash_password(data.new_password)
    update_user_password(current_user["id"], new_hash)

    return {"message": "Password changed successfully"}

@router.post("/reset-password/{token}")
async def reset_password_with_token(token: str, data: PasswordResetConfirm):
    """Reset password using a reset token."""
    user = get_user_by_reset_token(token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Check if token is expired
    expires = datetime.fromisoformat(user["reset_token_expires"])
    if datetime.utcnow() > expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )

    # Update password
    new_hash = hash_password(data.new_password)
    update_user_password(user["id"], new_hash)

    return {"message": "Password reset successfully"}
