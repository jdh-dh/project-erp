"""릴리즈 이력 서비스."""
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ConflictError, NotFoundError
from app.core.logging import get_logger
from app.models import Release
from app.models.change_log import ACTION_CREATE, ACTION_DEACTIVATE, ACTION_UPDATE
from app.schemas.release import ReleaseCreate, ReleaseUpdate
from app.services import change_log_service, project_service

logger = get_logger(__name__)


def release_to_dict(release: Release) -> dict:
    return {
        "id": release.id,
        "version": release.version,
        "title": release.title,
        "release_date": release.release_date,
        "content": release.content,
        "created_by": release.created_by,
        "creator_name": release.creator.name,
    }


def get_release(db: Session, project_id: int, release_id: int) -> Release:
    release = db.scalar(
        select(Release)
        .where(Release.id == release_id, Release.project_id == project_id)
        .options(selectinload(Release.creator))
    )
    if not release or not release.is_active:
        raise NotFoundError("릴리즈를 찾을 수 없습니다.")
    return release


def list_releases(db: Session, project_id: int) -> list[Release]:
    project_service.get_project(db, project_id)
    return list(
        db.scalars(
            select(Release)
            .where(Release.project_id == project_id, Release.is_active.is_(True))
            .options(selectinload(Release.creator))
            .order_by(Release.release_date.desc(), Release.id.desc())
        ).all()
    )


def _check_version(
    db: Session, project_id: int, version: str, *, exclude_id: int | None = None
) -> None:
    query = select(Release.id).where(
        Release.project_id == project_id,
        Release.version == version,
        Release.is_active.is_(True),
    )
    if exclude_id is not None:
        query = query.where(Release.id != exclude_id)
    if db.scalar(query):
        raise ConflictError("같은 릴리즈 버전이 이미 있습니다.", code="RELEASE_DUPLICATED")


def create_release(
    db: Session, project_id: int, data: ReleaseCreate, *, created_by: int
) -> Release:
    project_service.get_project(db, project_id)
    _check_version(db, project_id, data.version)

    release = Release(project_id=project_id, created_by=created_by, **data.model_dump())
    db.add(release)
    db.flush()
    change_log_service.record(
        db,
        entity_type="release",
        entity_id=release.id,
        action=ACTION_CREATE,
        changed_by=created_by,
        after_data=change_log_service.snapshot(release),
    )
    db.commit()
    logger.info("release created: id=%s project_id=%s v=%s", release.id, project_id, release.version)
    return get_release(db, project_id, release.id)


def update_release(
    db: Session, project_id: int, release_id: int, data: ReleaseUpdate, *, changed_by: int
) -> Release:
    release = get_release(db, project_id, release_id)
    payload = data.model_dump(exclude_unset=True)
    if "version" in payload:
        _check_version(db, project_id, payload["version"], exclude_id=release_id)

    before = change_log_service.snapshot(release)
    for field, value in payload.items():
        setattr(release, field, value)
    change_log_service.record(
        db,
        entity_type="release",
        entity_id=release.id,
        action=ACTION_UPDATE,
        changed_by=changed_by,
        before_data=before,
        after_data=change_log_service.snapshot(release),
    )
    db.commit()
    return get_release(db, project_id, release_id)


def deactivate_release(db: Session, project_id: int, release_id: int, *, changed_by: int) -> None:
    release = get_release(db, project_id, release_id)
    before = change_log_service.snapshot(release)
    release.is_active = False
    change_log_service.record(
        db,
        entity_type="release",
        entity_id=release.id,
        action=ACTION_DEACTIVATE,
        changed_by=changed_by,
        before_data=before,
        after_data=change_log_service.snapshot(release),
    )
    db.commit()
