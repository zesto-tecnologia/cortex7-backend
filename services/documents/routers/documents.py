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
from shared.models.documento import Documento
from services.documents.schemas.documento import (
    DocumentoCreate,
    DocumentoUpdate,
    DocumentoResponse,
)
from services.documents.services.document_processor import DocumentProcessor
from services.documents.services.embedding_service import EmbeddingService

router = APIRouter()

document_processor = DocumentProcessor()
embedding_service = EmbeddingService()


@router.get("/", response_model=List[DocumentoResponse])
async def list_documents(
    empresa_id: UUID,
    departamento: Optional[str] = None,
    tipo: Optional[str] = None,
    status: Optional[str] = "ativo",
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List documents with filters."""
    query = select(Documento).where(
        Documento.empresa_id == empresa_id,
        Documento.status == status
    )

    if departamento:
        query = query.where(Documento.departamento == departamento)

    if tipo:
        query = query.where(Documento.tipo == tipo)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{document_id}", response_model=DocumentoResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific document."""
    result = await db.execute(
        select(Documento).where(Documento.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@router.post("/upload", response_model=DocumentoResponse)
async def upload_document(
    empresa_id: UUID = Form(...),
    departamento: str = Form(...),
    tipo: str = Form(...),
    titulo: str = Form(...),
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
        arquivo_url = f"s3://bucket/{empresa_id}/{file.filename}"

        # Create document record
        document = Documento(
            empresa_id=empresa_id,
            departamento=departamento,
            tipo=tipo,
            titulo=titulo,
            conteudo_original=extracted_text,
            metadata=metadata_dict,
            arquivo_url=arquivo_url,
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


@router.post("/", response_model=DocumentoResponse)
async def create_document(
    document: DocumentoCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a document record without file upload."""
    # Generate embedding if content is provided
    embedding = None
    if document.conteudo_original:
        embedding = await embedding_service.generate_embedding(
            document.conteudo_original
        )

    db_document = Documento(
        **document.dict(exclude={'conteudo_original'}),
        conteudo_original=document.conteudo_original,
        embedding=embedding
    )

    db.add(db_document)
    await db.commit()
    await db.refresh(db_document)
    return db_document


@router.put("/{document_id}", response_model=DocumentoResponse)
async def update_document(
    document_id: UUID,
    document_update: DocumentoUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a document."""
    result = await db.execute(
        select(Documento).where(Documento.id == document_id)
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
        select(Documento).where(Documento.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    document.status = "inativo"
    await db.commit()

    return {"message": "Document deleted successfully"}