from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import User
from app.schemas.document import DocumentCreate, DocumentOut, DocumentUpdate
from app.services import document_service
from app.services.document_service import doc_to_dict

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["documents"])

admin_or_manager = require_roles("admin", "manager")


@router.get("", response_model=list[DocumentOut])
def list_documents(
    project_id: int,
    doc_type: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    docs = document_service.list_documents(db, project_id, doc_type=doc_type)
    return [doc_to_dict(d) for d in docs]


@router.post("", response_model=DocumentOut, status_code=201)
def create_document(
    project_id: int,
    body: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    doc = document_service.create_document(db, project_id, body, author_id=current_user.id)
    return doc_to_dict(doc)


@router.patch("/{doc_id}", response_model=DocumentOut)
def update_document(
    project_id: int,
    doc_id: int,
    body: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    doc = document_service.update_document(
        db, project_id, doc_id, body, changed_by=current_user.id
    )
    return doc_to_dict(doc)


@router.patch("/{doc_id}/deactivate", status_code=204)
def deactivate_document(
    project_id: int,
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    document_service.deactivate_document(db, project_id, doc_id, changed_by=current_user.id)
