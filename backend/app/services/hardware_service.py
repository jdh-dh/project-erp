"""하드웨어 관리(보드, BOM, 제작 이력) 서비스."""
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ConflictError, NotFoundError
from app.core.logging import get_logger
from app.models import BomItem, HwBoard, HwFabrication
from app.models.change_log import ACTION_CREATE, ACTION_DEACTIVATE, ACTION_UPDATE
from app.schemas.hardware import (
    BoardCreate,
    BoardUpdate,
    BomItemCreate,
    BomItemUpdate,
    FabricationCreate,
)
from app.services import change_log_service, project_service

logger = get_logger(__name__)


def _active_bom(board: HwBoard) -> list[BomItem]:
    return [i for i in board.bom_items if i.is_active]


def board_detail_dict(board: HwBoard) -> dict:
    return {
        "id": board.id,
        "name": board.name,
        "revision": board.revision,
        "status": board.status,
        "description": board.description,
        "bom_items": _active_bom(board),
        "fabrications": sorted(
            board.fabrications, key=lambda f: (f.fab_date, f.id), reverse=True
        ),
    }


def get_board(db: Session, project_id: int, board_id: int, *, with_detail: bool = False) -> HwBoard:
    query = select(HwBoard).where(
        HwBoard.id == board_id, HwBoard.project_id == project_id
    )
    if with_detail:
        query = query.options(
            selectinload(HwBoard.bom_items), selectinload(HwBoard.fabrications)
        )
    board = db.scalar(query)
    if not board or not board.is_active:
        raise NotFoundError("보드를 찾을 수 없습니다.")
    return board


def list_boards(db: Session, project_id: int) -> list[HwBoard]:
    project_service.get_project(db, project_id)
    return list(
        db.scalars(
            select(HwBoard)
            .where(HwBoard.project_id == project_id, HwBoard.is_active.is_(True))
            .order_by(HwBoard.name, HwBoard.revision)
        ).all()
    )


def _check_name_revision(
    db: Session, project_id: int, name: str, revision: str, *, exclude_id: int | None = None
) -> None:
    query = select(HwBoard.id).where(
        HwBoard.project_id == project_id,
        HwBoard.name == name,
        HwBoard.revision == revision,
        HwBoard.is_active.is_(True),
    )
    if exclude_id is not None:
        query = query.where(HwBoard.id != exclude_id)
    if db.scalar(query):
        raise ConflictError(
            "같은 이름과 리비전의 보드가 이미 있습니다.", code="BOARD_DUPLICATED"
        )


def create_board(db: Session, project_id: int, data: BoardCreate, *, changed_by: int) -> dict:
    project_service.get_project(db, project_id)
    _check_name_revision(db, project_id, data.name, data.revision)

    board = HwBoard(project_id=project_id, **data.model_dump())
    db.add(board)
    db.flush()
    change_log_service.record(
        db,
        entity_type="hw_board",
        entity_id=board.id,
        action=ACTION_CREATE,
        changed_by=changed_by,
        after_data=change_log_service.snapshot(board),
    )
    db.commit()
    logger.info("hw board created: id=%s project_id=%s", board.id, project_id)
    return board_detail_dict(get_board(db, project_id, board.id, with_detail=True))


def update_board(
    db: Session, project_id: int, board_id: int, data: BoardUpdate, *, changed_by: int
) -> dict:
    board = get_board(db, project_id, board_id)
    payload = data.model_dump(exclude_unset=True)
    name = payload.get("name", board.name)
    revision = payload.get("revision", board.revision)
    if "name" in payload or "revision" in payload:
        _check_name_revision(db, project_id, name, revision, exclude_id=board_id)

    before = change_log_service.snapshot(board)
    for field, value in payload.items():
        setattr(board, field, value)
    change_log_service.record(
        db,
        entity_type="hw_board",
        entity_id=board.id,
        action=ACTION_UPDATE,
        changed_by=changed_by,
        before_data=before,
        after_data=change_log_service.snapshot(board),
    )
    db.commit()
    return board_detail_dict(get_board(db, project_id, board_id, with_detail=True))


def deactivate_board(db: Session, project_id: int, board_id: int, *, changed_by: int) -> None:
    """보드 논리 삭제. BOM 항목도 함께 비활성화 (REQ-HW-007)."""
    board = get_board(db, project_id, board_id, with_detail=True)
    before = change_log_service.snapshot(board)
    board.is_active = False
    for item in _active_bom(board):
        item.is_active = False
    change_log_service.record(
        db,
        entity_type="hw_board",
        entity_id=board.id,
        action=ACTION_DEACTIVATE,
        changed_by=changed_by,
        before_data=before,
        after_data=change_log_service.snapshot(board),
    )
    db.commit()
    logger.info("hw board deactivated: id=%s", board_id)


def add_bom_item(
    db: Session, project_id: int, board_id: int, data: BomItemCreate, *, changed_by: int
) -> BomItem:
    board = get_board(db, project_id, board_id)
    item = BomItem(board_id=board.id, **data.model_dump())
    db.add(item)
    db.flush()
    change_log_service.record(
        db,
        entity_type="bom_item",
        entity_id=item.id,
        action=ACTION_CREATE,
        changed_by=changed_by,
        after_data=change_log_service.snapshot(item),
    )
    db.commit()
    db.refresh(item)
    return item


def _get_bom_item(db: Session, project_id: int, board_id: int, item_id: int) -> BomItem:
    get_board(db, project_id, board_id)
    item = db.scalar(
        select(BomItem).where(BomItem.id == item_id, BomItem.board_id == board_id)
    )
    if not item or not item.is_active:
        raise NotFoundError("BOM 부품을 찾을 수 없습니다.")
    return item


def update_bom_item(
    db: Session,
    project_id: int,
    board_id: int,
    item_id: int,
    data: BomItemUpdate,
    *,
    changed_by: int,
) -> BomItem:
    item = _get_bom_item(db, project_id, board_id, item_id)
    before = change_log_service.snapshot(item)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    change_log_service.record(
        db,
        entity_type="bom_item",
        entity_id=item.id,
        action=ACTION_UPDATE,
        changed_by=changed_by,
        before_data=before,
        after_data=change_log_service.snapshot(item),
    )
    db.commit()
    db.refresh(item)
    return item


def deactivate_bom_item(
    db: Session, project_id: int, board_id: int, item_id: int, *, changed_by: int
) -> None:
    item = _get_bom_item(db, project_id, board_id, item_id)
    before = change_log_service.snapshot(item)
    item.is_active = False
    change_log_service.record(
        db,
        entity_type="bom_item",
        entity_id=item.id,
        action=ACTION_DEACTIVATE,
        changed_by=changed_by,
        before_data=before,
        after_data=change_log_service.snapshot(item),
    )
    db.commit()


def add_fabrication(
    db: Session, project_id: int, board_id: int, data: FabricationCreate, *, changed_by: int
) -> HwFabrication:
    board = get_board(db, project_id, board_id)
    fab = HwFabrication(board_id=board.id, **data.model_dump())
    db.add(fab)
    db.flush()
    change_log_service.record(
        db,
        entity_type="hw_fabrication",
        entity_id=fab.id,
        action=ACTION_CREATE,
        changed_by=changed_by,
        after_data=change_log_service.snapshot(fab),
    )
    db.commit()
    db.refresh(fab)
    logger.info("fabrication added: board_id=%s qty=%s", board_id, fab.quantity)
    return fab
