"""Pydantic schemas for authentication."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=200)
    password: str = Field(..., min_length=6, max_length=100)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=200)
    password: str = Field(..., min_length=8, max_length=100)
    nickname: str = Field(..., min_length=1, max_length=100)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800


class UserResponse(BaseModel):
    id: str
    username: str
    nickname: str = ""
    role: str = "operator"
    is_active: bool = True
    created_at: str = ""

    model_config = {"from_attributes": True}
