"""
Pydantic schemas for Workflow and Task management.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class WorkflowCreate(BaseModel):
    """Schema for creating a workflow."""
    company_id: UUID
    workflow_type: str = Field(..., max_length=50)
    input_data: Optional[Dict[str, Any]] = None
    priority: str = Field(default="normal", pattern="^(low|normal|high)$")


class WorkflowUpdate(BaseModel):
    """Schema for updating a workflow."""
    status: Optional[str] = Field(None, pattern="^(pending|running|completed|failed|cancelled)$")
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class WorkflowResponse(BaseModel):
    """Schema for workflow response."""
    id: UUID
    company_id: UUID
    workflow_type: str
    status: str
    input_data: Optional[Dict[str, Any]]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    celery_task_id: Optional[str]
    priority: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    """Schema for creating a task."""
    company_id: UUID
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    type: Optional[str] = Field(None, max_length=50)
    assigned_to: Optional[UUID] = None
    workflow_id: Optional[UUID] = None
    prioridade: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")
    due_date: Optional[str] = None


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed|cancelled)$")
    assigned_to: Optional[UUID] = None
    resultado: Optional[Dict[str, Any]] = None
    prioridade: Optional[str] = Field(None, pattern="^(low|normal|high|urgent)$")
    due_date: Optional[str] = None


class TaskResponse(BaseModel):
    """Schema for task response."""
    id: UUID
    company_id: UUID
    title: str
    description: Optional[str]
    type: Optional[str]
    status: str
    assigned_to: Optional[UUID]
    workflow_id: Optional[UUID]
    resultado: Optional[Dict[str, Any]]
    prioridade: str
    due_date: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

