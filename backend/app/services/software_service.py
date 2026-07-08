"""소프트웨어 관리(모듈, 버전, 빌드, 배포) 서비스."""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.core.logging import get_logger
from app.models import SwBuild, SwDeployment, SwModule, SwVersion
from app.models.change_log import ACTION_CREATE, ACTION_DEACTIVATE, ACTION_UPDATE
from app.schemas.software import (
    BuildCreate,
    DeploymentCreate,
    ModuleCreate,
    ModuleUpdate,
    VersionCreate,
    VersionUpdate,
)
from app.services import change_log_service, project_service

logger = get_logger(__name__)


# ---------- 모듈 ----------

def _active_versions(module: SwModule) -> list[SwVersion]:
    return sorted(
        (v for v in module.versions if v.is_active), key=lambda v: v.id, reverse=True
    )


def module_detail_dict(module: SwModule) -> dict:
    return {
        "id": module.id,
        "name": module.name,
        "module_type": module.module_type,
        "repo_url": module.repo_url,
        "description": module.description,
        "versions": _active_versions(module),
    }


def get_module(
    db: Session, project_id: int, module_id: int, *, with_versions: bool = False
) -> SwModule:
    query = select(SwModule).where(
        SwModule.id == module_id, SwModule.project_id == project_id
    )
    if with_versions:
        query = query.options(selectinload(SwModule.versions))
    module = db.scalar(query)
    if not module or not module.is_active:
        raise NotFoundError("모듈을 찾을 수 없습니다.")
    return module


def list_modules(db: Session, project_id: int) -> list[SwModule]:
    project_service.get_project(db, project_id)
    return list(
        db.scalars(
            select(SwModule)
            .where(SwModule.project_id == project_id, SwModule.is_active.is_(True))
            .order_by(SwModule.name)
        ).all()
    )


def _check_module_name(
    db: Session, project_id: int, name: str, *, exclude_id: int | None = None
) -> None:
    query = select(SwModule.id).where(
        SwModule.project_id == project_id,
        SwModule.name == name,
        SwModule.is_active.is_(True),
    )
    if exclude_id is not None:
        query = query.where(SwModule.id != exclude_id)
    if db.scalar(query):
        raise ConflictError("같은 이름의 모듈이 이미 있습니다.", code="MODULE_DUPLICATED")


def create_module(db: Session, project_id: int, data: ModuleCreate, *, changed_by: int) -> dict:
    project_service.get_project(db, project_id)
    _check_module_name(db, project_id, data.name)

    module = SwModule(project_id=project_id, **data.model_dump())
    db.add(module)
    db.flush()
    change_log_service.record(
        db,
        entity_type="sw_module",
        entity_id=module.id,
        action=ACTION_CREATE,
        changed_by=changed_by,
        after_data=change_log_service.snapshot(module),
    )
    db.commit()
    logger.info("sw module created: id=%s project_id=%s", module.id, project_id)
    return module_detail_dict(get_module(db, project_id, module.id, with_versions=True))


def update_module(
    db: Session, project_id: int, module_id: int, data: ModuleUpdate, *, changed_by: int
) -> dict:
    module = get_module(db, project_id, module_id)
    payload = data.model_dump(exclude_unset=True)
    if "name" in payload:
        _check_module_name(db, project_id, payload["name"], exclude_id=module_id)

    before = change_log_service.snapshot(module)
    for field, value in payload.items():
        setattr(module, field, value)
    change_log_service.record(
        db,
        entity_type="sw_module",
        entity_id=module.id,
        action=ACTION_UPDATE,
        changed_by=changed_by,
        before_data=before,
        after_data=change_log_service.snapshot(module),
    )
    db.commit()
    return module_detail_dict(get_module(db, project_id, module_id, with_versions=True))


def deactivate_module(db: Session, project_id: int, module_id: int, *, changed_by: int) -> None:
    module = get_module(db, project_id, module_id, with_versions=True)
    before = change_log_service.snapshot(module)
    module.is_active = False
    for version in module.versions:
        version.is_active = False
    change_log_service.record(
        db,
        entity_type="sw_module",
        entity_id=module.id,
        action=ACTION_DEACTIVATE,
        changed_by=changed_by,
        before_data=before,
        after_data=change_log_service.snapshot(module),
    )
    db.commit()
    logger.info("sw module deactivated: id=%s", module_id)


# ---------- 버전 ----------

def version_detail_dict(version: SwVersion) -> dict:
    return {
        "id": version.id,
        "version": version.version,
        "status": version.status,
        "released_date": version.released_date,
        "note": version.note,
        "builds": sorted(version.builds, key=lambda b: b.id, reverse=True),
        "deployments": sorted(version.deployments, key=lambda d: d.id, reverse=True),
    }


def get_version(
    db: Session, project_id: int, module_id: int, version_id: int, *, with_detail: bool = False
) -> SwVersion:
    get_module(db, project_id, module_id)
    query = select(SwVersion).where(
        SwVersion.id == version_id, SwVersion.module_id == module_id
    )
    if with_detail:
        query = query.options(
            selectinload(SwVersion.builds), selectinload(SwVersion.deployments)
        )
    version = db.scalar(query)
    if not version or not version.is_active:
        raise NotFoundError("버전을 찾을 수 없습니다.")
    return version


def _check_version_string(
    db: Session, module_id: int, version_str: str, *, exclude_id: int | None = None
) -> None:
    query = select(SwVersion.id).where(
        SwVersion.module_id == module_id,
        SwVersion.version == version_str,
        SwVersion.is_active.is_(True),
    )
    if exclude_id is not None:
        query = query.where(SwVersion.id != exclude_id)
    if db.scalar(query):
        raise ConflictError("같은 버전이 이미 있습니다.", code="VERSION_DUPLICATED")


def create_version(
    db: Session, project_id: int, module_id: int, data: VersionCreate, *, changed_by: int
) -> SwVersion:
    get_module(db, project_id, module_id)
    _check_version_string(db, module_id, data.version)

    version = SwVersion(module_id=module_id, **data.model_dump())
    db.add(version)
    db.flush()
    change_log_service.record(
        db,
        entity_type="sw_version",
        entity_id=version.id,
        action=ACTION_CREATE,
        changed_by=changed_by,
        after_data=change_log_service.snapshot(version),
    )
    db.commit()
    db.refresh(version)
    logger.info("sw version created: id=%s module_id=%s", version.id, module_id)
    return version


def update_version(
    db: Session,
    project_id: int,
    module_id: int,
    version_id: int,
    data: VersionUpdate,
    *,
    changed_by: int,
) -> SwVersion:
    version = get_version(db, project_id, module_id, version_id)
    payload = data.model_dump(exclude_unset=True)
    if "version" in payload:
        _check_version_string(db, module_id, payload["version"], exclude_id=version_id)

    before = change_log_service.snapshot(version)
    for field, value in payload.items():
        setattr(version, field, value)
    change_log_service.record(
        db,
        entity_type="sw_version",
        entity_id=version.id,
        action=ACTION_UPDATE,
        changed_by=changed_by,
        before_data=before,
        after_data=change_log_service.snapshot(version),
    )
    db.commit()
    db.refresh(version)
    return version


def release_version(
    db: Session, project_id: int, module_id: int, version_id: int, *, changed_by: int
) -> SwVersion:
    """릴리즈 처리 (REQ-SW-005): 상태 RELEASED, 릴리즈일 기록."""
    version = get_version(db, project_id, module_id, version_id)
    if version.status == "RELEASED":
        raise AppError("이미 릴리즈된 버전입니다.", code="ALREADY_RELEASED")
    before = change_log_service.snapshot(version)
    version.status = "RELEASED"
    version.released_date = date.today()
    change_log_service.record(
        db,
        entity_type="sw_version",
        entity_id=version.id,
        action=ACTION_UPDATE,
        changed_by=changed_by,
        before_data=before,
        after_data=change_log_service.snapshot(version),
    )
    db.commit()
    db.refresh(version)
    logger.info("sw version released: id=%s", version_id)
    return version


# ---------- 빌드 / 배포 ----------

def add_build(
    db: Session,
    project_id: int,
    module_id: int,
    version_id: int,
    data: BuildCreate,
    *,
    changed_by: int,
) -> SwBuild:
    version = get_version(db, project_id, module_id, version_id)
    build = SwBuild(version_id=version.id, **data.model_dump())
    db.add(build)
    db.flush()
    change_log_service.record(
        db,
        entity_type="sw_build",
        entity_id=build.id,
        action=ACTION_CREATE,
        changed_by=changed_by,
        after_data=change_log_service.snapshot(build),
    )
    db.commit()
    db.refresh(build)
    return build


def add_deployment(
    db: Session,
    project_id: int,
    module_id: int,
    version_id: int,
    data: DeploymentCreate,
    *,
    changed_by: int,
) -> SwDeployment:
    version = get_version(db, project_id, module_id, version_id)
    deployment = SwDeployment(version_id=version.id, **data.model_dump())
    db.add(deployment)
    db.flush()
    change_log_service.record(
        db,
        entity_type="sw_deployment",
        entity_id=deployment.id,
        action=ACTION_CREATE,
        changed_by=changed_by,
        after_data=change_log_service.snapshot(deployment),
    )
    db.commit()
    db.refresh(deployment)
    logger.info(
        "sw deployment added: version_id=%s env=%s", version_id, deployment.environment
    )
    return deployment
