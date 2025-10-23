"""
Celery tasks for async workflow execution.
"""

import logging
from celery import Celery
from sqlalchemy import select
from uuid import UUID

from shared.config.settings import Settings
from shared.database.connection import AsyncSessionLocal
from shared.models.workflow import Workflow

# Initialize Celery
settings = Settings()
celery_app = Celery(
    "cortex_workflows",
    broker=settings.celery_broker_url,
    backend=settings.celery_backend_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

logger = logging.getLogger(__name__)


async def update_workflow_status(workflow_id: str, status: str, result: dict = None, error: str = None):
    """Update workflow status in database."""
    async with AsyncSessionLocal() as session:
        result_db = await session.execute(
            select(Workflow).where(Workflow.id == UUID(workflow_id))
        )
        workflow = result_db.scalar_one_or_none()
        
        if workflow:
            workflow.status = status
            if result:
                workflow.result = result
            if error:
                workflow.error_message = error
            
            await session.commit()


@celery_app.task(bind=True)
def execute_general_workflow(self, workflow_id: str, empresa_id: str, task_description: str):
    """Execute a general task workflow asynchronously."""
    import asyncio
    from langchain_openai import ChatOpenAI
    from ..crews.general_task_crew import create_general_task_crew
    
    try:
        # Update status to running
        asyncio.run(update_workflow_status(workflow_id, "running"))
        
        # Initialize LLM
        llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0.7)
        
        # Create and execute crew
        crew = create_general_task_crew(llm, empresa_id, task_description)
        result = crew.kickoff()

        # Append flow diagram to the result
        flow_diagram = getattr(crew, '_flow_diagram', '')
        print(flow_diagram)
        final_result = str(result) + "\n" + flow_diagram

        # Update status to completed
        asyncio.run(update_workflow_status(
            workflow_id,
            "completed",
            result={"output": final_result}
        ))

        return {"status": "completed", "result": final_result}
        
    except Exception as e:
        logger.error(f"Error executing general workflow: {e}", exc_info=True)
        asyncio.run(update_workflow_status(
            workflow_id,
            "failed",
            error=str(e)
        ))
        raise


@celery_app.task(bind=True)
def execute_financial_analysis(self, workflow_id: str, empresa_id: str, analysis_type: str):
    """Execute a financial analysis workflow asynchronously."""
    import asyncio
    from langchain_openai import ChatOpenAI
    from ..crews.financial_analysis_crew import create_financial_analysis_crew
    
    try:
        asyncio.run(update_workflow_status(workflow_id, "running"))
        
        llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0.3)
        crew = create_financial_analysis_crew(llm, empresa_id, analysis_type)
        result = crew.kickoff()
        
        asyncio.run(update_workflow_status(
            workflow_id,
            "completed",
            result={"output": str(result), "analysis_type": analysis_type}
        ))
        
        return {"status": "completed", "result": str(result)}
        
    except Exception as e:
        logger.error(f"Error executing financial analysis: {e}", exc_info=True)
        asyncio.run(update_workflow_status(workflow_id, "failed", error=str(e)))
        raise


@celery_app.task(bind=True)
def execute_document_review(self, workflow_id: str, empresa_id: str, query: str, review_type: str = "general"):
    """Execute a document review workflow asynchronously."""
    import asyncio
    from langchain_openai import ChatOpenAI
    from ..crews.document_review_crew import create_document_review_crew
    
    try:
        asyncio.run(update_workflow_status(workflow_id, "running"))
        
        llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0.3)
        crew = create_document_review_crew(llm, empresa_id, query, review_type)
        result = crew.kickoff()
        
        asyncio.run(update_workflow_status(
            workflow_id,
            "completed",
            result={"output": str(result), "query": query, "review_type": review_type}
        ))
        
        return {"status": "completed", "result": str(result)}
        
    except Exception as e:
        logger.error(f"Error executing document review: {e}", exc_info=True)
        asyncio.run(update_workflow_status(workflow_id, "failed", error=str(e)))
        raise

