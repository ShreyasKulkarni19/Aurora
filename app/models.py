"""Data models for the QA service."""

from pydantic import BaseModel, Field
from typing import Optional, List


class Message(BaseModel):
    """Message model from the messages API."""
    id: str
    user_id: str
    user_name: str
    timestamp: str  # ISO 8601 timestamp string
    message: str


class MessagesResponse(BaseModel):
    """Response model from the messages API."""
    total: int
    items: List[Message] = Field(default_factory=list)


class QuestionRequest(BaseModel):
    """Request model for the QA endpoint."""
    question: str = Field(..., description="Natural language question to answer")


class AnswerResponse(BaseModel):
    """Response model for the QA endpoint."""
    answer: str = Field(..., description="Answer to the question")


class DetailedAnswerResponse(BaseModel):
    """Detailed response model for the QA endpoint with sources."""
    answer: str = Field(..., description="Answer to the question")
    sources: Optional[List[str]] = Field(
        default=None,
        description="Source message IDs used for the answer"
    )


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = None

