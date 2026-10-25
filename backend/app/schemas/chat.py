from typing import Optional, List
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    conversation_id: Optional[int] = None
    message: str = Field(..., min_length=1, max_length=8000)


class ChatResponse(BaseModel):
    conversation_id: int
    user_message_id: int
    assistant_message_id: int
    content: str
    title: str


class HealthResponse(BaseModel):
    status: str
    provider: str
    model: str
    configured: bool
