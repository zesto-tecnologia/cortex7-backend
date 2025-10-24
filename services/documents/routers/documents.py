"""
Documents router for CRUD operations.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
import json

from shared.database.connection import get_db
from shared.models.document import Document
from services.documents.schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
)
from services.documents.services.document_processor import DocumentProcessor
from services.documents.services.embedding_service import EmbeddingService

router = APIRouter()

document_processor = DocumentProcessor()
embedding_service = EmbeddingService()


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    company_id: UUID,
    department: Optional[str] = None,
    type: Optional[str] = None,
    status: Optional[str] = "active",
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List documents with filters."""
    query = select(Document).where(
        Document.company_id == company_id,
        Document.status == status
    )

    if department:
        query = query.where(Document.department == department)

    if type:
        query = query.where(Document.type == type)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific document."""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    company_id: UUID = Form(...),
    departament: str = Form(...),
    type: str = Form(...),
    title: str = Form(...),
    metadata: str = Form("{}"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload and process a document."""
    try:
        # Parse metadata
        metadata_dict = json.loads(metadata)

        # Process the document (extract text, etc.)
        file_content = await file.read()
        extracted_text = await document_processor.extract_text(
            file_content,
            file.filename
        )

        # Generate embedding for the text
        embedding = await embedding_service.generate_embedding(extracted_text)

        # TODO: Upload file to S3 and get URL
        file_url = f"s3://bucket/{company_id}/{file.filename}"

        # Create document record
        document = Document(
            company_id=company_id,
            department=departament,
            type=type,
            title=title,
            original_content=extracted_text,
            metadata=metadata_dict,
            file_url=file_url,
            embedding=embedding,
        )

        db.add(document)
        await db.commit()
        await db.refresh(document)

        return document

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid metadata JSON")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=DocumentResponse)
async def create_document(
    document: DocumentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a document record without file upload."""
    # Generate embedding if content is provided
    embedding = None
    if document.original_content:
        embedding = await embedding_service.generate_embedding(
            document.original_content
        )

    db_document = Document(
        **document.dict(exclude={'original_content'}),
        original_content=document.original_content,
        embedding=embedding
    )

    db.add(db_document)
    await db.commit()
    await db.refresh(db_document)
    return db_document


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: UUID,
    document_update: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a document."""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Update fields
    for field, value in document_update.dict(exclude_unset=True).items():
        setattr(document, field, value)

    # Regenerate embedding if content was updated
    if document_update.conteudo_original:
        document.embedding = await embedding_service.generate_embedding(
            document_update.conteudo_original
        )

    await db.commit()
    await db.refresh(document)
    return document


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a document (soft delete by changing status)."""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    document.status = "inactive"
    await db.commit()

    return {"message": "Document deleted successfully"}