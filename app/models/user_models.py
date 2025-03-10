from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, Numeric, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, EmailStr, Field, validator, HttpUrl
from typing import Optional, List, Dict, Any
import uuid
import datetime
from passlib.context import CryptContext
import secrets
import string

from app.core.database import Base

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# SQLAlchemy Models
class User(Base):
    """SQLAlchemy model for users."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    
    # Additional profile information
    avatar_url = Column(String)
    bio = Column(Text)
    company = Column(String)
    website = Column(String)
    location = Column(String)
    phone = Column(String)
    preferences = Column(JSON, default={})
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    
    # Usage limits and billing
    api_quota = Column(Integer, default=1000)  # Monthly API call limit
    tokens_used = Column(Integer, default=0)
    total_cost = Column(Numeric(10, 2), default=0)  # Total cost in USD
    billing_status = Column(String, default="free")  # free, premium, enterprise
    subscription_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    last_active = Column(DateTime(timezone=True))
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    usage_records = relationship("UsageRecord", back_populates="user", cascade="all, delete-orphan")
    chat_history = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")
    contexts = relationship("UserContext", back_populates="user", cascade="all, delete-orphan")
    
    def verify_password(self, plain_password):
        """Verify a plain password against the hashed password."""
        return pwd_context.verify(plain_password, self.hashed_password)
    
    @staticmethod
    def get_password_hash(password):
        """Hash a password for storing."""
        return pwd_context.hash(password)


class APIKey(Base):
    """SQLAlchemy model for API keys."""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    usage_records = relationship("UsageRecord", back_populates="api_key", cascade="all, delete-orphan")
    
    @staticmethod
    def generate_key():
        """Generate a new API key."""
        return f"sk-{uuid.uuid4().hex}"


class UsageRecord(Base):
    """SQLAlchemy model for tracking API usage."""
    __tablename__ = "usage_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=True)
    endpoint = Column(String, nullable=False)
    tokens_used = Column(Integer, default=0)
    cost = Column(Numeric(10, 4), default=0)  # Cost in USD
    model = Column(String)
    status = Column(String)
    response_time = Column(Float)  # Response time in seconds
    error_message = Column(Text)
    request_metadata = Column(JSON, default={})  # Additional request metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="usage_records")
    api_key = relationship("APIKey", back_populates="usage_records")


# Pydantic Models for API
class UserProfile(BaseModel):
    """Pydantic model for user profile information."""
    avatar_url: Optional[HttpUrl] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    website: Optional[HttpUrl] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    preferences: Dict[str, Any] = {}


class UserBase(BaseModel):
    """Base Pydantic model for user data."""
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    profile: Optional[UserProfile] = None


class UserCreate(UserBase):
    """Pydantic model for user creation."""
    password: str
    
    @validator('password')
    def password_strength(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(char in string.punctuation for char in v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserUpdate(BaseModel):
    """Pydantic model for user updates."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    profile: Optional[UserProfile] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """Pydantic model for user in database."""
    id: int
    is_active: bool
    is_superuser: bool
    is_verified: bool
    email_verified: bool
    api_quota: int
    tokens_used: int
    total_cost: float
    billing_status: str
    subscription_expires: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    last_login: Optional[datetime.datetime] = None
    last_active: Optional[datetime.datetime] = None
    
    class Config:
        from_attributes = True


class UserResponse(UserInDB):
    """Pydantic model for user response."""
    pass


class Token(BaseModel):
    """Pydantic model for authentication token."""
    access_token: str
    token_type: str
    user: UserResponse


class TokenData(BaseModel):
    """Pydantic model for token data."""
    user_id: int
    exp: Optional[datetime.datetime] = None


class APIKeyBase(BaseModel):
    """Base Pydantic model for API key."""
    name: str
    expires_at: Optional[datetime.datetime] = None


class APIKeyCreate(APIKeyBase):
    """Pydantic model for API key creation."""
    pass


class APIKeyInDB(APIKeyBase):
    """Pydantic model for API key in database."""
    id: int
    key: str
    user_id: int
    is_active: bool
    created_at: datetime.datetime
    expires_at: Optional[datetime.datetime] = None
    last_used_at: Optional[datetime.datetime] = None
    
    class Config:
        from_attributes = True


class APIKeyResponse(APIKeyBase):
    """Pydantic model for API key response."""
    id: int
    key: str
    is_active: bool
    created_at: datetime.datetime
    expires_at: Optional[datetime.datetime] = None
    last_used_at: Optional[datetime.datetime] = None
    
    class Config:
        from_attributes = True


class UsageRecordBase(BaseModel):
    """Base Pydantic model for usage record."""
    endpoint: str
    tokens_used: int = 0
    cost: float = 0
    model: Optional[str] = None
    status: Optional[str] = None
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    request_metadata: Dict[str, Any] = {}


class UsageRecordCreate(UsageRecordBase):
    """Pydantic model for usage record creation."""
    user_id: int
    api_key_id: Optional[int] = None


class UsageRecordInDB(UsageRecordBase):
    """Pydantic model for usage record in database."""
    id: int
    user_id: int
    api_key_id: Optional[int] = None
    created_at: datetime.datetime
    
    class Config:
        from_attributes = True


class UsageRecordResponse(UsageRecordInDB):
    """Pydantic model for usage record response."""
    pass


class UsageSummary(BaseModel):
    """Pydantic model for usage summary."""
    total_requests: int
    total_tokens: int
    total_cost: float
    models_used: List[str]
    endpoints_used: List[str]
    average_response_time: float
    error_rate: float
    usage_by_day: Dict[str, int]
    cost_by_model: Dict[str, float] 