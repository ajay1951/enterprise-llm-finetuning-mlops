from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: Optional[str]
    status: str
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True

class RefreshTokenRequest(BaseModel):
    refresh_token: str
