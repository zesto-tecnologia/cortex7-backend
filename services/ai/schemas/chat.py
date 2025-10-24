"""
Chat request/response schemas for AI service.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID


class ChatMessage(BaseModel):
    """Single chat message."""
    
    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content")
    

class ChatRequest(BaseModel):
    """Request for chat endpoint."""
    
    message: str = Field(..., description="User message")
    company_id: UUID = Field(..., description="Company ID for context")
    conversation_history: Optional[List[ChatMessage]] = Field(
        default=None,
        description="Previous conversation history"
    )
    is_async: bool = Field(
        default=False,
        description="Whether to execute asynchronously"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata"
    )


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    
    response: str = Field(..., description="AI agent response")
    workflow_id: Optional[str] = Field(
        None,
        description="Workflow ID if task was sent to background"
    )
    is_async: bool = Field(
        default=False,
        description="Whether the task is running asynchronously"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional response metadata"
    )


class ChatStreamChunk(BaseModel):
    """Streaming chunk for chat responses."""
    
    chunk: str = Field(..., description="Text chunk")
    done: bool = Field(default=False, description="Whether streaming is complete")
    error: Optional[str] = Field(None, description="Error message if any")

