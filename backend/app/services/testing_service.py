"""시험 관리(케이스, 실행 결과) 서비스."""
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models import TestCase, TestRun
from app.models.change_log import ACTION_CREATE, ACTION_DEACTIVATE, ACTION_UPDATE
from app.schemas.testing import TestCaseCreate, TestCaseUpdate, TestRunCreate
from app.services import change_log_service, project_service

logger = get_logger(__name__)


def _run_to_dict(run: TestRun) -> dict:
    return {
        "id": run.id,
        "run_date": run.run_date,
        "result": run.result,
        "tester_id": run.tester_id,
        "tester_name": run.tester.name,
        "note": run.note,
    }


def case_detail_dict(case: TestCase) -> dict:
    return {
        "id": case.id,
        "test_type": case.test_type,
        "name": case.name,
        "description": case.description,
        "expected_result": case.expected_result,
        "last_result": case.last_result,
        "runs": [_run_to_dict(r) for r in sorted(case.runs, key=lambda r: r.id, reverse=True)],
    }


def get_case(db: Session, project_id: int, case_id: int, *, with_runs: bool = False) -> TestCase:
    query = select(TestCase).where(
        TestCase.id == case_id, TestCase.project_id == project_id
    )
    if with_runs:
        query = query.options(selectinload(TestCase.runs).selectinload(TestRun.tester))
    else:
        query = query.options(selectinload(TestCase.runs))
    case = db.scalar(query)
    if not case or not case.is_active:
        raise NotFoundError("시험 케이스를 찾을 수 없습니다.")
    return case


def list_cases(db: Session, project_id: int, *, test_type: str | None = None) -> list[TestCase]:
    project_service.get_project(db, project_id)
    query = (
        select(TestCase)
        .where(TestCase.project_id == project_id, TestCase.is_active.is_(True))
        .options(selectinload(TestCase.runs))
        .order_by(TestCase.id)
    )
    if test_type:
        query = query.where(TestCase.test_type == test_type)
    return list(db.scalars(query).all())


def create_case(db: Session, project_id: int, data: TestCaseCreate, *, changed_by: int) -> TestCase:
    project_service.get_project(db, project_id)
    case = TestCase(project_id=project_id, **data.model_dump())
    db.add(case)
    db.flush()
    change_log_service.record(
        db,
        entity_type="test_case",
        entity_id=case.id,
        action=ACTION_CREATE,
        changed_by=changed_by,
        after_data=change_log_service.snapshot(case),
    )
    db.commit()
    logger.info("test case created: id=%s project_id=%s", case.id, project_id)
    return get_case(db, project_id, case.id, with_runs=True)


def update_case(
    db: Session, project_id: int, case_id: int, data: TestCaseUpdate, *, changed_by: int
) -> TestCase:
    case = get_case(db, project_id, case_id)
    before = change_log_service.snapshot(case)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(case, field, value)
    change_log_service.record(
        db,
        entity_type="test_case",
        entity_id=case.id,
        action=ACTION_UPDATE,
        changed_by=changed_by,
        before_data=before,
        after_data=change_log_service.snapshot(case),
    )
    db.commit()
    return get_case(db, project_id, case_id, with_runs=True)


def deactivate_case(db: Session, project_id: int, case_id: int, *, changed_by: int) -> None:
    case = get_case(db, project_id, case_id)
    before = change_log_service.snapshot(case)
    case.is_active = False
    change_log_service.record(
        db,
        entity_type="test_case",
        entity_id=case.id,
        action=ACTION_DEACTIVATE,
        changed_by=changed_by,
        before_data=before,
        after_data=change_log_service.snapshot(case),
    )
    db.commit()


def add_run(
    db: Session, project_id: int, case_id: int, data: TestRunCreate, *, tester_id: int
) -> dict:
    """시험 실행 결과 기록. 시험자는 현재 사용자로 자동 기록 (REQ-TEST-003)."""
    case = get_case(db, project_id, case_id)
    run = TestRun(test_case_id=case.id, tester_id=tester_id, **data.model_dump())
    db.add(run)
    db.flush()
    change_log_service.record(
        db,
        entity_type="test_run",
        entity_id=run.id,
        action=ACTION_CREATE,
        changed_by=tester_id,
        after_data=change_log_service.snapshot(run),
    )
    db.commit()
    db.refresh(run)
    logger.info("test run added: case_id=%s result=%s", case_id, run.result)
    return _run_to_dict(run)
