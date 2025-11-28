from typing import List
from datetime import datetime, UTC
import io

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from PyPDF2 import PdfReader

from app.api.schemas import DocumentInput
from app.api.deps import get_document_service, get_container
from app.application.services.document_service import DocumentService
from app.core.container import AppContainer

router = APIRouter(tags=["documents"])


@router.post("/ingest")
async def ingest_document(
    doc: DocumentInput,
    container: AppContainer = Depends(get_container),
    document_service: DocumentService = Depends(get_document_service),
):
    try:
        vector = container.embeddings.embed(doc.content)
        doc_id = await document_service.ingest_document(doc.content, doc.metadata or {})
        payload = {
            "content": doc.content,
            "metadata": doc.metadata or {},
            "ingested_at": datetime.now(UTC).isoformat(),
        }
        await document_service.ingest_with_vector(doc_id, vector, payload)
        return {"id": doc_id, "message": "Document ingested successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")


@router.post("/batch_ingest")
async def batch_ingest(
    documents: List[DocumentInput],
    container: AppContainer = Depends(get_container),
    document_service: DocumentService = Depends(get_document_service),
):
    results = []
    for doc in documents:
        try:
            vector = container.embeddings.embed(doc.content)
            doc_id = await document_service.ingest_document(doc.content, doc.metadata or {})
            payload = {
                "content": doc.content,
                "metadata": doc.metadata or {},
                "ingested_at": datetime.now(UTC).isoformat(),
            }
            await document_service.ingest_with_vector(doc_id, vector, payload)
            results.append({"id": doc_id, "status": "success"})
        except Exception as e:
            results.append({"status": "error", "error": str(e)})
    return {"results": results}


@router.get("/documents")
async def list_documents(
    limit: int = 10,
    document_service: DocumentService = Depends(get_document_service),
):
    try:
        docs = await document_service.list_documents(limit=limit)
        return {"documents": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {e}")


@router.post("/upload/pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    container: AppContainer = Depends(get_container),
    document_service: DocumentService = Depends(get_document_service),
):
    """
    Upload and ingest a PDF file.
    The PDF will be parsed and each page will be stored as a separate document.
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Read PDF content
        pdf_bytes = await file.read()
        pdf_file = io.BytesIO(pdf_bytes)
        
        # Parse PDF
        pdf_reader = PdfReader(pdf_file)
        total_pages = len(pdf_reader.pages)
        
        results = []
        for page_num, page in enumerate(pdf_reader.pages, start=1):
            try:
                # Extract text from page
                text = page.extract_text()
                
                if not text.strip():
                    results.append({
                        "page": page_num,
                        "status": "skipped",
                        "reason": "No text found"
                    })
                    continue
                
                # Create metadata
                metadata = {
                    "filename": file.filename,
                    "page_number": page_num,
                    "total_pages": total_pages,
                    "content_type": "application/pdf"
                }
                
                # Generate embedding and ingest
                vector = container.embeddings.embed(text)
                doc_id = await document_service.ingest_document(text, metadata)
                payload = {
                    "content": text,
                    "metadata": metadata,
                    "ingested_at": datetime.now(UTC).isoformat(),
                }
                await document_service.ingest_with_vector(doc_id, vector, payload)
                
                results.append({
                    "page": page_num,
                    "id": doc_id,
                    "status": "success",
                    "chars": len(text)
                })
            except Exception as e:
                results.append({
                    "page": page_num,
                    "status": "error",
                    "error": str(e)
                })
        
        successful = sum(1 for r in results if r["status"] == "success")
        
        return {
            "filename": file.filename,
            "total_pages": total_pages,
            "successful_pages": successful,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF upload failed: {str(e)}")


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    document_service: DocumentService = Depends(get_document_service),
):
    try:
        await document_service.delete_document(doc_id)
        return {"message": f"Document {doc_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion failed: {e}")
