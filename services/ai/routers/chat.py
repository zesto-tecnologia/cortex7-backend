"""
Chat endpoint for synchronous AI interactions.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_openai import ChatOpenAI
import logging
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..schemas.chat import ChatRequest, ChatResponse, ChatStreamChunk
from ..crews.simple_crew import create_simple_crew
from ..crews.general_task_crew import create_general_task_crew
from ..crews.financial_analysis_crew import create_financial_analysis_crew
from ..crews.document_review_crew import create_document_review_crew
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
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

        # Determine if this should be async or sync
        is_complex = request.is_async or any(word in request.message.lower() for word in [
            "analyze", "review", "comprehensive", "detailed", "report"
        ])

        if is_complex and request.is_async:
            # Trigger async workflow
            task = execute_general_workflow.delay(
                workflow_id=None,
                empresa_id=str(request.empresa_id),
                task_description=request.message
            )

            return ChatResponse(
                response="Your request has been queued for processing. You can check the status using the workflow ID.",
                workflow_id=task.id,
                is_async=True
            )

        # Synchronous execution with simple crew
        crew = create_simple_crew(llm, str(request.empresa_id), request.message)
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
    Streaming chat endpoint for real-time responses with step-by-step agent feedback.
    """
    # Shared queue for agent step updates
    step_queue = asyncio.Queue()

    # Get the event loop reference before creating the callback
    loop = asyncio.get_event_loop()

    def task_callback_fn(task_output):
        """Callback triggered after each task completion"""
        try:
            logger.info(f"Task callback triggered! Output: {task_output}")

            # Get task info
            task_desc = getattr(task_output, 'description', 'Unknown task')
            output_result = getattr(task_output, 'raw', str(task_output))
            agent_info = getattr(task_output, 'agent', 'Unknown agent')

            # Create step update message
            step_update = {
                'type': 'agent_step',
                'agent': str(agent_info),
                'task': str(task_desc)[:200],  # Limit task description length
                'output': str(output_result)[:500] if output_result else '',  # Limit output length
                'done': False
            }

            logger.info(f"Queueing task completion: {step_update}")
            asyncio.run_coroutine_threadsafe(step_queue.put(step_update), loop)
        except Exception as e:
            logger.error(f"Error in task callback: {e}", exc_info=True)

    def step_callback_fn(step_output):
        """Callback triggered after each agent step"""
        try:
            logger.info(f"Step callback triggered! Step: {step_output}")

            # Step output contains thought, action, observation
            step_str = str(step_output)[:300]

            # Send a lightweight update (don't flood with every tiny step)
            if len(step_str) > 20:  # Only send meaningful steps
                step_update = {
                    'type': 'agent_step',
                    'agent': 'Processing',
                    'task': step_str,
                    'output': '',
                    'done': False
                }
                asyncio.run_coroutine_threadsafe(step_queue.put(step_update), loop)
        except Exception as e:
            logger.error(f"Error in step callback: {e}", exc_info=True)

    async def generate():
        try:
            # Send initial status message
            yield f"data: {json.dumps({'chunk': '', 'status': 'initializing', 'done': False})}\n\n"

            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, streaming=True)

            # Use general task crew for streaming
            crew = create_general_task_crew(llm, str(request.empresa_id), request.message)

            # Set crew-level callbacks
            crew.task_callback = task_callback_fn
            crew.step_callback = step_callback_fn

            # Also add task-level callbacks
            for task in crew.tasks:
                task.callback = task_callback_fn

            logger.info(f"Crew created with {len(crew.tasks)} tasks and callbacks configured")

            # Execute crew in thread pool to prevent blocking
            executor = ThreadPoolExecutor(max_workers=1)

            # Start the crew execution in background
            crew_future = loop.run_in_executor(executor, crew.kickoff)

            # Stream agent steps and keep-alive messages while processing
            last_keepalive = asyncio.get_event_loop().time()

            while not crew_future.done():
                try:
                    # Try to get step updates from queue (non-blocking with timeout)
                    step_update = await asyncio.wait_for(step_queue.get(), timeout=0.5)
                    logger.info(f"Sending step update to client: {step_update}")
                    yield f"data: {json.dumps(step_update)}\n\n"
                    last_keepalive = asyncio.get_event_loop().time()
                except asyncio.TimeoutError:
                    # No step update, send keep-alive if needed
                    current_time = asyncio.get_event_loop().time()
                    if current_time - last_keepalive > 3:
                        yield f"data: {json.dumps({'chunk': '', 'status': 'processing', 'done': False})}\n\n"
                        last_keepalive = current_time

            # Process any remaining step updates
            logger.info(f"Processing remaining step updates, queue size: {step_queue.qsize()}")
            while not step_queue.empty():
                step_update = await step_queue.get()
                logger.info(f"Sending remaining step update: {step_update}")
                yield f"data: {json.dumps(step_update)}\n\n"

            # Get the result
            result = await crew_future

            # Stream the result in chunks
            result_str = str(result)
            chunk_size = 50

            for i in range(0, len(result_str), chunk_size):
                chunk = result_str[i:i + chunk_size]
                yield f"data: {json.dumps({'chunk': chunk, 'done': False})}\n\n"

            # Send the flow diagram after the main content
            flow_diagram = getattr(crew, '_flow_diagram', '')
            if flow_diagram:
                yield f"data: {json.dumps({'chunk': flow_diagram, 'done': False, 'type': 'flow_diagram'})}\n\n"

            yield f"data: {json.dumps({'chunk': '', 'done': True})}\n\n"

        except Exception as e:
            logger.error(f"Error in streaming chat: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

