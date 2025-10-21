"""
Pydantic schemas for Workflow and Task management.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class WorkflowCreate(BaseModel):
    """Schema for creating a workflow."""
    empresa_id: UUID
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
    empresa_id: UUID
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


class TarefaCreate(BaseModel):
    """Schema for creating a task."""
    empresa_id: UUID
    titulo: str = Field(..., max_length=255)
    descricao: Optional[str] = None
    tipo: Optional[str] = Field(None, max_length=50)
    atribuido_a: Optional[UUID] = None
    workflow_id: Optional[UUID] = None
    prioridade: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")
    data_vencimento: Optional[str] = None


class TarefaUpdate(BaseModel):
    """Schema for updating a task."""
    titulo: Optional[str] = Field(None, max_length=255)
    descricao: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed|cancelled)$")
    atribuido_a: Optional[UUID] = None
    resultado: Optional[Dict[str, Any]] = None
    prioridade: Optional[str] = Field(None, pattern="^(low|normal|high|urgent)$")
    data_vencimento: Optional[str] = None


class TarefaResponse(BaseModel):
    """Schema for task response."""
    id: UUID
    empresa_id: UUID
    titulo: str
    descricao: Optional[str]
    tipo: Optional[str]
    status: str
    atribuido_a: Optional[UUID]
    workflow_id: Optional[UUID]
    resultado: Optional[Dict[str, Any]]
    prioridade: str
    data_vencimento: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

