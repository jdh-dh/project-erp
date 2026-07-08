from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import User
from app.schemas.hardware import (
    BoardCreate,
    BoardDetailOut,
    BoardOut,
    BoardUpdate,
    BomItemCreate,
    BomItemOut,
    BomItemUpdate,
    FabricationCreate,
    FabricationOut,
)
from app.services import hardware_service
from app.services.hardware_service import board_detail_dict

router = APIRouter(prefix="/projects/{project_id}/hw", tags=["hardware"])

admin_or_manager = require_roles("admin", "manager")


@router.get("/boards", response_model=list[BoardOut])
def list_boards(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return hardware_service.list_boards(db, project_id)


@router.post("/boards", response_model=BoardDetailOut, status_code=201)
def create_board(
    project_id: int,
    body: BoardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    return hardware_service.create_board(db, project_id, body, changed_by=current_user.id)


@router.get("/boards/{board_id}", response_model=BoardDetailOut)
def get_board(
    project_id: int,
    board_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    board = hardware_service.get_board(db, project_id, board_id, with_detail=True)
    return board_detail_dict(board)


@router.patch("/boards/{board_id}", response_model=BoardDetailOut)
def update_board(
    project_id: int,
    board_id: int,
    body: BoardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    return hardware_service.update_board(
        db, project_id, board_id, body, changed_by=current_user.id
    )


@router.patch("/boards/{board_id}/deactivate", status_code=204)
def deactivate_board(
    project_id: int,
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    hardware_service.deactivate_board(db, project_id, board_id, changed_by=current_user.id)


@router.post("/boards/{board_id}/bom", response_model=BomItemOut, status_code=201)
def add_bom_item(
    project_id: int,
    board_id: int,
    body: BomItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    return hardware_service.add_bom_item(
        db, project_id, board_id, body, changed_by=current_user.id
    )


@router.patch("/boards/{board_id}/bom/{item_id}", response_model=BomItemOut)
def update_bom_item(
    project_id: int,
    board_id: int,
    item_id: int,
    body: BomItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    return hardware_service.update_bom_item(
        db, project_id, board_id, item_id, body, changed_by=current_user.id
    )


@router.patch("/boards/{board_id}/bom/{item_id}/deactivate", status_code=204)
def deactivate_bom_item(
    project_id: int,
    board_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    hardware_service.deactivate_bom_item(
        db, project_id, board_id, item_id, changed_by=current_user.id
    )


@router.post(
    "/boards/{board_id}/fabrications", response_model=FabricationOut, status_code=201
)
def add_fabrication(
    project_id: int,
    board_id: int,
    body: FabricationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    return hardware_service.add_fabrication(
        db, project_id, board_id, body, changed_by=current_user.id
    )
