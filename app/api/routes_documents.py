from typing import List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends

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
            "ingested_at": datetime.utcnow().isoformat(),
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
                "ingested_at": datetime.utcnow().isoformat(),
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
