"""
Auth request/response schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    # Always the same response regardless of whether the email exists,
    # to prevent account enumeration.
    detail: str = "If an account exists for that email, a reset link is on its way."


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=10, max_length=256)
    password: str = Field(min_length=8, max_length=128)


class ResetPasswordResponse(BaseModel):
    detail: str = "Password updated."
