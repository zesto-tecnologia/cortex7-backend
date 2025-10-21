"""
Workflow management endpoints for async AI processing.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID, uuid4

from shared.database.connection import get_db
from shared.models.workflow import Workflow
from ..schemas.workflow import WorkflowCreate, WorkflowResponse, WorkflowUpdate
from ..tasks.workflow_tasks import (
    execute_general_workflow,
    execute_financial_analysis,
    execute_document_review,
)

router = APIRouter()


@router.post("/trigger", response_model=WorkflowResponse)
async def trigger_workflow(
    workflow_type: str,
    empresa_id: UUID,
    input_data: dict,
    priority: str = "normal",
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger an async workflow execution.
    
    Workflow types:
    - general: General task execution
    - financial_analysis: Financial analysis workflow
    - document_review: Document review and analysis
    """
    # Create workflow record
    workflow = Workflow(
        id=uuid4(),
        empresa_id=empresa_id,
        workflow_type=workflow_type,
        status="pending",
        input_data=input_data,
        priority=priority,
    )
    
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)
    
    # Trigger appropriate Celery task
    try:
        if workflow_type == "general":
            task = execute_general_workflow.delay(
                workflow_id=str(workflow.id),
                empresa_id=str(empresa_id),
                task_description=input_data.get("task_description", "")
            )
        elif workflow_type == "financial_analysis":
            task = execute_financial_analysis.delay(
                workflow_id=str(workflow.id),
                empresa_id=str(empresa_id),
                analysis_type=input_data.get("analysis_type", "general")
            )
        elif workflow_type == "document_review":
            task = execute_document_review.delay(
                workflow_id=str(workflow.id),
                empresa_id=str(empresa_id),
                query=input_data.get("query", ""),
                review_type=input_data.get("review_type", "general")
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown workflow type: {workflow_type}")
        
        # Update workflow with Celery task ID
        workflow.celery_task_id = task.id
        await db.commit()
        await db.refresh(workflow)
        
        return workflow
        
    except Exception as e:
        workflow.status = "failed"
        workflow.error_message = str(e)
        await db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get workflow status and results."""
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return workflow


@router.get("/", response_model=List[WorkflowResponse])
async def list_workflows(
    empresa_id: UUID,
    status: Optional[str] = None,
    workflow_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List workflows for a company."""
    query = select(Workflow).where(Workflow.empresa_id == empresa_id)
    
    if status:
        query = query.where(Workflow.status == status)
    
    if workflow_type:
        query = query.where(Workflow.workflow_type == workflow_type)
    
    query = query.order_by(Workflow.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.delete("/{workflow_id}")
async def cancel_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Cancel a pending or running workflow."""
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if workflow.status in ["completed", "failed", "cancelled"]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel workflow with status: {workflow.status}")
    
    # Cancel Celery task if exists
    if workflow.celery_task_id:
        from ..tasks.workflow_tasks import celery_app
        celery_app.control.revoke(workflow.celery_task_id, terminate=True)
    
    workflow.status = "cancelled"
    await db.commit()
    
    return {"message": "Workflow cancelled successfully", "workflow_id": str(workflow_id)}

