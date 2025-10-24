"""
Embeddings management router.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from shared.database.connection import get_db
from shared.models.audit import EmbeddingCache as CacheEmbedding
from services.documents.services.embedding_service import EmbeddingService
from services.documents.schemas.embedding import (
    EmbeddingRequest,
    EmbeddingResponse,
    BatchEmbeddingRequest,
)

router = APIRouter()
embedding_service = EmbeddingService()


@router.post("/generate", response_model=EmbeddingResponse)
async def generate_embedding(
    request: EmbeddingRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate embedding for a given text.
    """
    try:
        # Check cache first
        text_hash = embedding_service.hash_text(request.text)

        result = await db.execute(
            select(CacheEmbedding).where(CacheEmbedding.hash == text_hash)
        )
        cached = result.scalar_one_or_none()

        if cached:
            return EmbeddingResponse(
                text=request.text,
                embedding=cached.embedding.tolist(),
                model=cached.model,
                cached=True
            )

        # Generate new embedding
        embedding = await embedding_service.generate_embedding(request.text)

        # Cache the embedding
        cache_entry = CacheEmbedding(
            texto=request.text[:1000],  # Store first 1000 chars for reference
            hash=text_hash,
            embedding=embedding,
            modelo=request.model or "text-embedding-ada-002"
        )
        db.add(cache_entry)
        await db.commit()

        return EmbeddingResponse(
            text=request.text,
            embedding=embedding.tolist(),
            model=request.model or "text-embedding-ada-002",
            cached=False
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation error: {str(e)}")


@router.post("/generate-batch", response_model=List[EmbeddingResponse])
async def generate_batch_embeddings(
    request: BatchEmbeddingRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate embeddings for multiple texts.
    """
    try:
        results = []

        for text in request.texts:
            # Check cache
            text_hash = embedding_service.hash_text(text)

            result = await db.execute(
                select(CacheEmbedding).where(CacheEmbedding.hash == text_hash)
            )
            cached = result.scalar_one_or_none()

            if cached:
                results.append(EmbeddingResponse(
                    text=text,
                    embedding=cached.embedding.tolist(),
                    model=cached.model,
                    cached=True
                ))
            else:
                # Generate new embedding
                embedding = await embedding_service.generate_embedding(text)

                # Cache it
                cache_entry = CacheEmbedding(
                    text=text[:1000],
                    hash=text_hash,
                    embedding=embedding,
                    model=request.model or "text-embedding-ada-002"
                )
                db.add(cache_entry)

                results.append(EmbeddingResponse(
                    text=text,
                    embedding=embedding.tolist(),
                    model=request.model or "text-embedding-ada-002",
                    cached=False
                ))

        await db.commit()
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch embedding error: {str(e)}")


@router.post("/regenerate/{document_id}")
async def regenerate_document_embedding(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Regenerate embedding for a specific document.
    """
    from shared.models.document import Document

    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.original_content:
        raise HTTPException(status_code=400, detail="Document has no content to embed")

    try:
        # Generate new embedding
        new_embedding = await embedding_service.generate_embedding(
            document.original_content
        )

        document.embedding = new_embedding
        await db.commit()

        return {
            "message": "Embedding regenerated successfully",
            "document_id": document_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding regeneration error: {str(e)}")


@router.get("/cache/stats")
async def get_cache_statistics(
    db: AsyncSession = Depends(get_db),
):
    """
    Get embedding cache statistics.
    """
    from sqlalchemy import func

    result = await db.execute(
        select(
            func.count(CacheEmbedding.id).label("total_cached"),
            func.min(CacheEmbedding.created_at).label("oldest_entry"),
            func.max(CacheEmbedding.created_at).label("newest_entry")
        )
    )
    stats = result.fetchone()

    return {
        "total_cached_embeddings": stats.total_cached or 0,
        "oldest_entry": stats.oldest_entry,
        "newest_entry": stats.newest_entry
    }