"""
API Gateway for the Cortex microservices architecture.
"""

import httpx
import logging
import uvicorn
from typing import Any, Dict
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from shared.config.settings import settings
from cortex_auth import require_auth, require_admin, get_current_user
from cortex_auth.models import User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Cortex API Gateway",
    description="API Gateway for Corporate Agent System",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service routing configuration
SERVICE_ROUTES = {
    "/auth": settings.auth_service_url,
    "/financial": settings.financial_service_url,
    "/hr": settings.hr_service_url,
    "/legal": settings.legal_service_url,
    "/procurement": settings.procurement_service_url,
    "/documents": settings.documents_service_url,
    "/ai": settings.ai_service_url,
}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Cortex API Gateway",
        "version": "1.0.0",
        "status": "operational",
        "services": list(SERVICE_ROUTES.keys()),
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    services_health = {}

    async with httpx.AsyncClient() as client:
        for service_path, service_url in SERVICE_ROUTES.items():
            try:
                response = await client.get(f"{service_url}/health", timeout=5.0)
                services_health[service_path] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "status_code": response.status_code,
                }
            except Exception as e:
                services_health[service_path] = {
                    "status": "unreachable",
                    "error": str(e),
                }

    # Overall health is healthy only if all services are healthy
    overall_healthy = all(
        s.get("status") == "healthy" for s in services_health.values()
    )

    return {
        "gateway": "healthy",
        "services": services_health,
        "overall": "healthy" if overall_healthy else "degraded",
    }


@app.get("/api/profile")
@require_auth
async def get_user_profile(user: User = Depends(get_current_user)):
    """
    Get current user profile (authenticated route example).

    This demonstrates cortex-auth integration using both decorator and dependency.
    """
    return {
        "user_id": str(user.user_id),
        "email": user.email,
        "name": user.name,
        "roles": user.roles,
        "permissions": user.permissions,
    }


@app.get("/api/admin/services")
@require_admin
async def admin_service_status(request: Request):
    """
    Admin-only endpoint to get detailed service status.

    Requires admin role to access.
    """
    user = request.state.user
    logger.info(f"Admin {user.email} accessing service status")

    services_info = {}
    async with httpx.AsyncClient() as client:
        for service_path, service_url in SERVICE_ROUTES.items():
            try:
                response = await client.get(f"{service_url}/health", timeout=5.0)
                services_info[service_path] = {
                    "url": service_url,
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "status_code": response.status_code,
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                }
            except Exception as e:
                services_info[service_path] = {
                    "url": service_url,
                    "status": "unreachable",
                    "error": str(e),
                }

    return {
        "admin": user.email,
        "services": services_info,
        "timestamp": httpx._utils.get_utc_now().isoformat(),
    }


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def gateway_proxy(request: Request, path: str):
    """
    Proxy requests to appropriate microservices.
    """
    logger.info(f"🔍 Gateway received request: {request.method} /{path}")

    # Determine which service to route to
    service_url = None
    for route_prefix, url in SERVICE_ROUTES.items():
        if f"/{path}".startswith(route_prefix):
            service_url = url
            # Remove the service prefix from the path
            service_path = f"/{path}".replace(route_prefix, "", 1)
            if not service_path:
                service_path = "/"
            break

    if not service_url:
        raise HTTPException(status_code=404, detail="Service not found")

    # Build the target URL
    target_url = f"{service_url}{service_path}"
    logger.info(f"🎯 Routing to: {target_url}")

    # Get query parameters
    query_params = dict(request.query_params)

    # Get headers (excluding host)
    headers = dict(request.headers)
    headers.pop("host", None)

    # Forward authentication cookies to downstream services
    # This ensures that authenticated requests maintain their auth context
    # The downstream services can use cortex-auth to validate the same token

    # Get body for POST/PUT/PATCH requests
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.body()

    try:
        # Check if this is a streaming endpoint
        is_streaming = "stream" in path
        logger.info(f"🔎 Streaming check: path='{path}', is_streaming={is_streaming}")

        if is_streaming:
            logger.info(f"🌊 STREAMING REQUEST DETECTED: {path} -> {target_url}")
            # For streaming endpoints, use StreamingResponse
            async def stream_proxy():
                logger.info(f"🚀 Starting stream proxy for {target_url}")
                chunk_count = 0
                async with httpx.AsyncClient(follow_redirects=True) as client:
                    async with client.stream(
                        method=request.method,
                        url=target_url,
                        params=query_params,
                        headers=headers,
                        content=body,
                        timeout=60.0,  # Longer timeout for streaming
                    ) as response:
                        logger.info(f"📡 Stream response status: {response.status_code}")
                        async for chunk in response.aiter_bytes():
                            chunk_count += 1
                            if chunk_count % 10 == 0:
                                logger.info(f"📦 Streamed {chunk_count} chunks so far...")
                            yield chunk
                logger.info(f"✅ Stream completed. Total chunks: {chunk_count}")

            return StreamingResponse(
                stream_proxy(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",  # Disable buffering in nginx if present
                }
            )
        else:
            # For regular endpoints, use JSONResponse
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.request(
                    method=request.method,
                    url=target_url,
                    params=query_params,
                    headers=headers,
                    content=body,
                    timeout=30.0,
                )

            # Return the response
            return JSONResponse(
                content=response.json() if response.content else None,
                status_code=response.status_code,
                headers=dict(response.headers),
            )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Service timeout")
    except httpx.RequestError as e:
        logger.error(f"Error proxying request to {target_url}: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal gateway error")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.gateway_port)