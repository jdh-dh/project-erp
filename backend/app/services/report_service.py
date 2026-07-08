"""프로젝트 종합 보고서 서비스 (읽기 전용, 실시간 집계)."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.logging import get_logger
from app.models import (
    HwBoard,
    Issue,
    Release,
    SwModule,
    SwVersion,
    TestCase,
)
from app.services import cost_service, project_service, schedule_service, testing_service

logger = get_logger(__name__)


def _count(db: Session, query) -> int:
    return db.scalar(select(func.count()).select_from(query.subquery())) or 0


def project_report(db: Session, project_id: int) -> dict:
    """REQ-RPT-001~003: 조회 시점 실시간 집계."""
    project = project_service.get_project(db, project_id, with_detail=True)

    # 이슈: 상태별 건수
    issues = db.scalars(
        select(Issue).where(Issue.project_id == project_id, Issue.is_active.is_(True))
    ).all()
    issue_stats = {
        "total": len(issues),
        "open": sum(1 for i in issues if i.status == "OPEN"),
        "in_progress": sum(1 for i in issues if i.status == "IN_PROGRESS"),
        "resolved": sum(1 for i in issues if i.status == "RESOLVED"),
        "closed": sum(1 for i in issues if i.status == "CLOSED"),
    }

    # 시험: 최근 결과 기준 (REQ-RPT-002)
    cases = testing_service.list_cases(db, project_id)
    last_results = [case.last_result for case in cases]
    test_stats = {
        "total": len(cases),
        "passed": last_results.count("PASS"),
        "failed": last_results.count("FAIL"),
        "blocked": last_results.count("BLOCKED"),
        "not_run": last_results.count(None),
    }

    # 하드웨어 / 소프트웨어 현황
    boards = _count(
        db,
        select(HwBoard.id).where(
            HwBoard.project_id == project_id, HwBoard.is_active.is_(True)
        ),
    )
    modules = db.scalars(
        select(SwModule)
        .where(SwModule.project_id == project_id, SwModule.is_active.is_(True))
        .options(selectinload(SwModule.versions))
    ).all()
    versions = [v for m in modules for v in m.versions if v.is_active]
    sw_stats = {
        "modules": len(modules),
        "versions": len(versions),
        "released_versions": sum(1 for v in versions if v.status == "RELEASED"),
    }

    releases = _count(
        db,
        select(Release.id).where(
            Release.project_id == project_id, Release.is_active.is_(True)
        ),
    )

    return {
        "project": {
            "code": project.code,
            "name": project.name,
            "project_type": project.project_type,
            "status": project.status,
            "customer_name": project.customer.name,
            "manager_name": project.manager.name,
            "start_date": project.start_date,
            "end_date": project.end_date,
        },
        "schedule": schedule_service.schedule_summary(db, project_id),
        "issues": issue_stats,
        "tests": test_stats,
        "hardware": {"boards": boards},
        "software": sw_stats,
        "releases": releases,
        "costs": cost_service.cost_summary(db, project_id),
    }
