"""
Documents microservice main application.
Handles document management with vector embeddings for semantic search.
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database.connection import get_db
from shared.config.settings import settings
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="Documents Service",
    description="Document management with vector embeddings and semantic search",
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
        "service": "Documents Service",
        "version": "1.0.0",
        "status": "operational",
        "features": [
            "document_upload",
            "text_extraction",
            "vector_embeddings",
            "semantic_search"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Import routers
from services.documents.routers import documents, search, embeddings

# Include routers
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(embeddings.router, prefix="/embeddings", tags=["Embeddings"])


if __name__ == "__main__":
    port = int(settings.documents_service_port)
    uvicorn.run(app, host="0.0.0.0", port=port)