"""
Chat endpoint for synchronous AI interactions.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_openai import ChatOpenAI
import logging
import json

from ..schemas.chat import ChatRequest, ChatResponse, ChatStreamChunk
from ..crews.general_task_crew import create_general_task_crew
from ..tasks.workflow_tasks import execute_general_workflow, execute_financial_analysis, execute_document_review

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Synchronous chat endpoint for quick interactions.
    
    For simple queries, executes immediately. For complex workflows,
    triggers async processing.
    """
    try:
        # Initialize LLM
        llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0.7)
        
        # Determine if this should be async or sync
        is_complex = request.is_async or any(word in request.message.lower() for word in [
            "analyze", "review", "comprehensive", "detailed", "report"
        ])
        
        if is_complex and request.is_async:
            # Trigger async workflow
            task = execute_general_workflow.delay(
                workflow_id=None,  # Will be created in task
                empresa_id=str(request.empresa_id),
                task_description=request.message
            )
            
            return ChatResponse(
                response="Your request has been queued for processing. You can check the status using the workflow ID.",
                workflow_id=task.id,
                is_async=True
            )
        
        # Synchronous execution for simple queries
        crew = create_general_task_crew(llm, str(request.empresa_id), request.message)
        result = crew.kickoff()
        
        return ChatResponse(
            response=str(result),
            workflow_id=None,
            is_async=False
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint for real-time responses.
    """
    async def generate():
        try:
            llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0.7, streaming=True)
            crew = create_general_task_crew(llm, str(request.empresa_id), request.message)
            
            # Execute crew and stream results
            result = crew.kickoff()
            
            # Stream the result in chunks
            result_str = str(result)
            chunk_size = 50
            
            for i in range(0, len(result_str), chunk_size):
                chunk = result_str[i:i + chunk_size]
                yield f"data: {json.dumps({'chunk': chunk, 'done': False})}\n\n"
            
            yield f"data: {json.dumps({'chunk': '', 'done': True})}\n\n"
            
        except Exception as e:
            logger.error(f"Error in streaming chat: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

