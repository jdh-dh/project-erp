"""변경 이력 기록/조회 서비스 (REQ-COM-001)."""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models import ChangeLog

logger = get_logger(__name__)

# 이력에 기록하지 않는 컬럼
_EXCLUDED_FIELDS = {"password_hash", "created_at", "updated_at"}


def snapshot(entity) -> dict:
    """SQLAlchemy 엔티티의 컬럼 값을 JSON 직렬화 가능한 dict로 변환한다."""
    data: dict = {}
    for column in entity.__table__.columns:
        if column.name in _EXCLUDED_FIELDS:
            continue
        value = getattr(entity, column.name)
        if isinstance(value, (datetime, date)):
            value = value.isoformat()
        elif isinstance(value, Decimal):
            value = str(value)
        data[column.name] = value
    return data


def record(
    db: Session,
    *,
    entity_type: str,
    entity_id: int,
    action: str,
    changed_by: int,
    before_data: dict | None = None,
    after_data: dict | None = None,
) -> ChangeLog:
    log = ChangeLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        changed_by=changed_by,
        before_data=before_data,
        after_data=after_data,
    )
    db.add(log)
    logger.info("change_log: %s#%s %s by user#%s", entity_type, entity_id, action, changed_by)
    return log


def list_logs(
    db: Session,
    *,
    entity_type: str | None = None,
    entity_id: int | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[ChangeLog], int]:
    query = select(ChangeLog)
    if entity_type:
        query = query.where(ChangeLog.entity_type == entity_type)
    if entity_id is not None:
        query = query.where(ChangeLog.entity_id == entity_id)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query.order_by(ChangeLog.id.desc()).offset((page - 1) * size).limit(size)
    ).all()
    return list(rows), total
