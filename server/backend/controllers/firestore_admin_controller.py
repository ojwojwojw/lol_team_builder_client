from fastapi import APIRouter, Body, Depends, HTTPException, Query

from ..models.request_models import (
    FirestoreDeleteDocumentsRequest,
    FirestoreDeleteOlderThanRequest,
)
from ..security import require_admin_user
from ..stores.firestore_admin_store import (
    clear_collection,
    delete_documents_by_ids,
    delete_older_than_days,
    get_collection_document,
    get_collection_stats,
    list_collection_documents,
)


router = APIRouter(prefix="/admin/firestore", tags=["firestore-admin"], dependencies=[Depends(require_admin_user)])


@router.get("/stats")
def get_stats():
    """Firestore 컬렉션별 문서 수와 대략적인 JSON 크기를 반환한다."""
    rows = get_collection_stats()
    return {
        "collections": rows,
        "collection_count": len(rows),
        "document_count": sum(row["documents"] for row in rows),
        "approx_json_bytes": sum(row["approx_json_bytes"] for row in rows),
    }


@router.get("/collections/{collection_name}/documents")
def get_documents(
    collection_name: str,
    limit: int = Query(50, ge=1, le=500),
):
    """선택한 컬렉션의 문서 목록을 제한 개수만큼 반환한다."""
    try:
        documents = list_collection_documents(collection_name, limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "collection": collection_name,
        "count": len(documents),
        "documents": documents,
    }


@router.get("/collections/{collection_name}/documents/{document_id}")
def get_document(collection_name: str, document_id: str):
    """선택한 Firestore 문서 한 건의 전체 JSON을 반환한다."""
    try:
        document = get_collection_document(collection_name, document_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@router.post("/delete-documents")
def delete_documents(req: FirestoreDeleteDocumentsRequest = Body(...)):
    """선택한 문서 ID 목록을 컬렉션에서 일괄 삭제한다."""
    try:
        result = delete_documents_by_ids(req.collection, req.document_ids)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "collection": req.collection,
        **result,
    }


@router.post("/clear-collection")
def clear_collection_documents(req: FirestoreDeleteDocumentsRequest = Body(...)):
    """문서 ID 목록 대신 컬렉션 전체 삭제를 수행한다."""
    try:
        return clear_collection(req.collection)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/delete-older-than")
def delete_collection_older_than(req: FirestoreDeleteOlderThanRequest = Body(...)):
    """지정한 일수보다 오래된 문서를 대표 시간 필드 기준으로 삭제한다."""
    try:
        return delete_older_than_days(req.collection, req.days)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
