from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.report import ProjectReport
from app.services import report_service

router = APIRouter(prefix="/projects/{project_id}/report", tags=["report"])


@router.get("", response_model=ProjectReport)
def project_report(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return report_service.project_report(db, project_id)
