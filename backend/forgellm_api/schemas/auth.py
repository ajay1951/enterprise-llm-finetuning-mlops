from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None


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
    name: str | None
    status: str
    created_at: datetime
    last_login_at: datetime | None

    class Config:
        from_attributes = True


class RefreshTokenRequest(BaseModel):
    refresh_token: str
