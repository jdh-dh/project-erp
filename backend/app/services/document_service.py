"""문서 관리 서비스."""
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models import Document
from app.models.change_log import ACTION_CREATE, ACTION_DEACTIVATE, ACTION_UPDATE
from app.schemas.document import DocumentCreate, DocumentUpdate
from app.services import change_log_service, project_service

logger = get_logger(__name__)


def doc_to_dict(doc: Document) -> dict:
    return {
        "id": doc.id,
        "doc_type": doc.doc_type,
        "title": doc.title,
        "version": doc.version,
        "file_url": doc.file_url,
        "description": doc.description,
        "author_id": doc.author_id,
        "author_name": doc.author.name,
        "updated_at": doc.updated_at,
    }


def get_document(db: Session, project_id: int, doc_id: int) -> Document:
    doc = db.scalar(
        select(Document)
        .where(Document.id == doc_id, Document.project_id == project_id)
        .options(selectinload(Document.author))
    )
    if not doc or not doc.is_active:
        raise NotFoundError("문서를 찾을 수 없습니다.")
    return doc


def list_documents(
    db: Session, project_id: int, *, doc_type: str | None = None
) -> list[Document]:
    project_service.get_project(db, project_id)
    query = (
        select(Document)
        .where(Document.project_id == project_id, Document.is_active.is_(True))
        .options(selectinload(Document.author))
        .order_by(Document.id.desc())
    )
    if doc_type:
        query = query.where(Document.doc_type == doc_type)
    return list(db.scalars(query).all())


def create_document(
    db: Session, project_id: int, data: DocumentCreate, *, author_id: int
) -> Document:
    project_service.get_project(db, project_id)
    doc = Document(project_id=project_id, author_id=author_id, **data.model_dump())
    db.add(doc)
    db.flush()
    change_log_service.record(
        db,
        entity_type="document",
        entity_id=doc.id,
        action=ACTION_CREATE,
        changed_by=author_id,
        after_data=change_log_service.snapshot(doc),
    )
    db.commit()
    logger.info("document created: id=%s project_id=%s", doc.id, project_id)
    return get_document(db, project_id, doc.id)


def update_document(
    db: Session, project_id: int, doc_id: int, data: DocumentUpdate, *, changed_by: int
) -> Document:
    doc = get_document(db, project_id, doc_id)
    before = change_log_service.snapshot(doc)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(doc, field, value)
    change_log_service.record(
        db,
        entity_type="document",
        entity_id=doc.id,
        action=ACTION_UPDATE,
        changed_by=changed_by,
        before_data=before,
        after_data=change_log_service.snapshot(doc),
    )
    db.commit()
    return get_document(db, project_id, doc_id)


def deactivate_document(db: Session, project_id: int, doc_id: int, *, changed_by: int) -> None:
    doc = get_document(db, project_id, doc_id)
    before = change_log_service.snapshot(doc)
    doc.is_active = False
    change_log_service.record(
        db,
        entity_type="document",
        entity_id=doc.id,
        action=ACTION_DEACTIVATE,
        changed_by=changed_by,
        before_data=before,
        after_data=change_log_service.snapshot(doc),
    )
    db.commit()
