"""
AI microservice main application.
Handles AI-powered analysis, chat, and intelligent automation.
"""

import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config.settings import settings

# Create FastAPI app
app = FastAPI(
    title="AI Service",
    description="AI-powered analysis and automation microservice",
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


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "AI Service",
        "version": "1.0.0",
        "status": "operational",
        "features": [
            "chat_interface",
            "document_analysis",
            "intelligent_agents",
            "workflow_automation"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Import routers
from services.ai.routers import chat

# Include routers
app.include_router(chat.router, prefix="/chat", tags=["Chat"])


if __name__ == "__main__":
    port = int(settings.ai_service_port)
    uvicorn.run("services.ai.main:app", host="0.0.0.0", port=port, reload=True)

