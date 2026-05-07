"""
Authentication related schemas for admin API
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Admin Schemas
class AdminBase(BaseModel):
    email: EmailStr

class AdminRegister(AdminBase):
    username: str
    email: EmailStr
    password: str

class AdminLogin(AdminBase):
    email: EmailStr
    password: str

# Admin Forgot Password Schemas
class AdminForgotPasswordEmailSchema(BaseModel):
    email: EmailStr

class AdminForgotPasswordVerifySchema(BaseModel):
    email: EmailStr
    otp: str

class AdminForgotPasswordResetSchema(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

# Admin Change Password Schema
class AdminChangePasswordSchema(BaseModel):
    old_password: str
    new_password: str

class AdminResponse(AdminBase):
    id: int
    is_active: bool
    created_at: datetime
    profile_image: Optional[str] = None
    bio: Optional[str] = None

# Admin Profile Update Schema
class AdminProfileUpdateSchema(BaseModel):
    profile_image: Optional[str] = None
    bio: Optional[str] = None
    name: Optional[str] = None
    email: Optional[EmailStr] = None

# Token Schema
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes in seconds

# Admin Token Management Schemas
class AdminRefreshTokenRequest(BaseModel):
    """Request schema for admin token refresh"""
    refresh_token: str

class AdminRefreshTokenResponse(BaseModel):
    """Response schema for admin token refresh"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class AdminLogoutRequest(BaseModel):
    """Request schema for admin logout"""
    refresh_token: str
