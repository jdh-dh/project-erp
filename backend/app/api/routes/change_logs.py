from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.change_log import ChangeLogOut
from app.schemas.common import Page
from app.services import change_log_service

router = APIRouter(prefix="/change-logs", tags=["change-logs"])


@router.get("", response_model=Page[ChangeLogOut])
def list_change_logs(
    entity_type: str | None = None,
    entity_id: int | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    logs, total = change_log_service.list_logs(
        db, entity_type=entity_type, entity_id=entity_id, page=page, size=size
    )
    items = [
        {
            "id": log.id,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "action": log.action,
            "changed_by": log.changed_by,
            "changed_by_name": log.changed_by_user.name,
            "changed_at": log.changed_at,
            "before_data": log.before_data,
            "after_data": log.after_data,
        }
        for log in logs
    ]
    return Page(items=items, total=total, page=page, size=size)
