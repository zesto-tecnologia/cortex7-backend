"""
Semantic search router using vector embeddings.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from shared.database.connection import get_db
from services.documents.services.embedding_service import EmbeddingService
from services.documents.schemas.search import (
    SearchQuery,
    SearchResult,
    SimilaritySearchQuery,
)

router = APIRouter()
embedding_service = EmbeddingService()


@router.post("/semantic", response_model=List[SearchResult])
async def semantic_search(
    query: SearchQuery,
    db: AsyncSession = Depends(get_db),
):
    """
    Perform semantic search using vector similarity.
    """
    try:
        # Generate embedding for the search query
        query_embedding = await embedding_service.generate_embedding(query.text)

        # Perform vector similarity search
        sql = text("""
            SELECT
                id,
                title,
                departamento,
                type,
                conteudo_original,
                metadata,
                file_url,
                1 - (embedding <=> :embedding::vector) as similarity
            FROM documents
            WHERE company_id = :company_id
                AND status = 'ativo'
                AND embedding IS NOT NULL
                {:departamento_filter}
                {:tipo_filter}
            ORDER BY embedding <=> :embedding::vector
            LIMIT :limit
        """.format(
            departamento_filter="AND departamento = :departamento" if query.departamento else "",
            tipo_filter="AND type = :type" if query.type else ""
        ))

        params = {
            "embedding": str(query_embedding),
            "company_id": str(query.company_id),
            "limit": query.limit or 10
        }

        if query.departamento:
            params["departamento"] = query.departamento
        if query.type:
            params["type"] = query.type

        result = await db.execute(sql, params)
        rows = result.fetchall()

        # Format results
        search_results = []
        for row in rows:
            # Only include results above similarity threshold
            if query.similarity_threshold and row.similarity < query.similarity_threshold:
                continue

            search_results.append(SearchResult(
                id=row.id,
                title=row.title,
                departamento=row.departamento,
                type=row.type,
                conteudo_preview=row.conteudo_original[:500] if row.conteudo_original else None,
                similarity_score=float(row.similarity),
                metadata=row.metadata,
                file_url=row.file_url
            ))

        return search_results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.post("/similar-documents", response_model=List[SearchResult])
async def find_similar_documents(
    query: SimilaritySearchQuery,
    db: AsyncSession = Depends(get_db),
):
    """
    Find documents similar to a given document.
    """
    try:
        # Get the source document's embedding
        source_doc_sql = text("""
            SELECT embedding
            FROM documents
            WHERE id = :document_id
        """)

        result = await db.execute(source_doc_sql, {"document_id": str(query.document_id)})
        row = result.fetchone()

        if not row or not row.embedding:
            raise HTTPException(status_code=404, detail="Document not found or has no embedding")

        # Find similar documents
        sql = text("""
            SELECT
                id,
                title,
                departamento,
                type,
                conteudo_original,
                metadata,
                file_url,
                1 - (embedding <=> :embedding::vector) as similarity
            FROM documents
            WHERE id != :document_id
                AND company_id = :company_id
                AND status = 'ativo'
                AND embedding IS NOT NULL
            ORDER BY embedding <=> :embedding::vector
            LIMIT :limit
        """)

        params = {
            "embedding": str(row.embedding),
            "document_id": str(query.document_id),
            "company_id": str(query.company_id),
            "limit": query.limit or 5
        }

        result = await db.execute(sql, params)
        rows = result.fetchall()

        # Format results
        search_results = []
        for row in rows:
            search_results.append(SearchResult(
                id=row.id,
                title=row.title,
                departamento=row.departamento,
                type=row.type,
                conteudo_preview=row.conteudo_original[:500] if row.conteudo_original else None,
                similarity_score=float(row.similarity),
                metadata=row.metadata,
                file_url=row.file_url
            ))

        return search_results

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.get("/by-metadata")
async def search_by_metadata(
    company_id: UUID,
    key: str,
    value: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Search documents by metadata key-value pairs.
    """
    sql = text("""
        SELECT id, title, departamento, type, metadata, file_url
        FROM documents
        WHERE company_id = :company_id
            AND status = 'ativo'
            AND metadata @> :search_json::jsonb
        LIMIT 100
    """)

    search_json = json.dumps({key: value})

    result = await db.execute(sql, {
        "company_id": str(company_id),
        "search_json": search_json
    })

    rows = result.fetchall()

    return [
        {
            "id": row.id,
            "title": row.title,
            "departamento": row.departamento,
            "type": row.type,
            "metadata": row.metadata,
            "file_url": row.file_url
        }
        for row in rows
    ]