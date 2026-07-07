from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import User
from app.schemas.common import Page
from app.schemas.customer import (
    ContactCreate,
    ContactOut,
    ContactUpdate,
    CustomerCreate,
    CustomerDetailOut,
    CustomerOut,
    CustomerUpdate,
)
from app.services import customer_service

router = APIRouter(prefix="/customers", tags=["customers"])

admin_or_manager = require_roles("admin", "manager")


@router.get("", response_model=Page[CustomerOut])
def list_customers(
    q: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items, total = customer_service.list_customers(db, q=q, page=page, size=size)
    return Page(items=items, total=total, page=page, size=size)


@router.post("", response_model=CustomerDetailOut, status_code=201)
def create_customer(
    body: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    return customer_service.create_customer(db, body, changed_by=current_user.id)


@router.get("/{customer_id}", response_model=CustomerDetailOut)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return customer_service.get_customer(db, customer_id, with_contacts=True)


@router.patch("/{customer_id}", response_model=CustomerDetailOut)
def update_customer(
    customer_id: int,
    body: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    return customer_service.update_customer(db, customer_id, body, changed_by=current_user.id)


@router.patch("/{customer_id}/deactivate", response_model=CustomerDetailOut)
def deactivate_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    return customer_service.deactivate_customer(db, customer_id, changed_by=current_user.id)


@router.post("/{customer_id}/contacts", response_model=ContactOut, status_code=201)
def add_contact(
    customer_id: int,
    body: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    return customer_service.add_contact(db, customer_id, body, changed_by=current_user.id)


@router.patch("/{customer_id}/contacts/{contact_id}", response_model=ContactOut)
def update_contact(
    customer_id: int,
    contact_id: int,
    body: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    return customer_service.update_contact(
        db, customer_id, contact_id, body, changed_by=current_user.id
    )
