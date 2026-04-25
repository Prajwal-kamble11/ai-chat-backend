from pydantic import BaseModel, EmailStr, field_validator, Field
from uuid import UUID
from typing import Optional, Literal
from datetime import datetime



# ================= USER =================
class UserCreate(BaseModel):
    clerk_user_id: str
    email: EmailStr


class UserResponse(BaseModel):
    id: UUID
    clerk_user_id: str
    email: EmailStr
    plan: str
    subscription_expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ================= CHAT =================

class ChatRequest(BaseModel):
    user_id: Optional[UUID] = None
    message: str = Field(..., max_length=1000)
    chat_id: Optional[UUID] = None

    @field_validator("message")
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()

class ChatResponse(BaseModel):
    chat_id: UUID
    user_message: str
    ai_response: str

# ================= MESSAGE =================
class MessageCreate(BaseModel):
    chat_id: Optional[UUID] = None
    user_id: UUID
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=1000)

    @field_validator("content")
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError("Content cannot be empty")
        return v.strip()

class MessageResponse(BaseModel):
    id: UUID
    chat_id: UUID
    role: str
    content: str
    created_at: datetime


    class Config:
        from_attributes = True