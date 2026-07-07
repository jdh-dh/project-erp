"""고객사 관리 서비스."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models import Customer, CustomerContact
from app.models.change_log import ACTION_CREATE, ACTION_DEACTIVATE, ACTION_UPDATE
from app.schemas.customer import (
    ContactCreate,
    ContactUpdate,
    CustomerCreate,
    CustomerUpdate,
)
from app.services import change_log_service

logger = get_logger(__name__)


def get_customer(db: Session, customer_id: int, *, with_contacts: bool = False) -> Customer:
    query = select(Customer).where(Customer.id == customer_id)
    if with_contacts:
        query = query.options(selectinload(Customer.contacts))
    customer = db.scalar(query)
    if not customer:
        raise NotFoundError("고객사를 찾을 수 없습니다.")
    return customer


def list_customers(
    db: Session, *, q: str | None = None, page: int = 1, size: int = 20
) -> tuple[list[Customer], int]:
    query = select(Customer)
    if q:
        query = query.where(Customer.name.ilike(f"%{q}%"))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query.order_by(Customer.id).offset((page - 1) * size).limit(size)
    ).all()
    return list(rows), total


def create_customer(db: Session, data: CustomerCreate, *, changed_by: int) -> Customer:
    customer = Customer(**data.model_dump())
    db.add(customer)
    db.flush()
    change_log_service.record(
        db,
        entity_type="customer",
        entity_id=customer.id,
        action=ACTION_CREATE,
        changed_by=changed_by,
        after_data=change_log_service.snapshot(customer),
    )
    db.commit()
    logger.info("customer created: id=%s name=%s", customer.id, customer.name)
    return get_customer(db, customer.id, with_contacts=True)


def update_customer(
    db: Session, customer_id: int, data: CustomerUpdate, *, changed_by: int
) -> Customer:
    customer = get_customer(db, customer_id)
    before = change_log_service.snapshot(customer)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(customer, field, value)
    change_log_service.record(
        db,
        entity_type="customer",
        entity_id=customer.id,
        action=ACTION_UPDATE,
        changed_by=changed_by,
        before_data=before,
        after_data=change_log_service.snapshot(customer),
    )
    db.commit()
    return get_customer(db, customer_id, with_contacts=True)


def deactivate_customer(db: Session, customer_id: int, *, changed_by: int) -> Customer:
    """고객사 비활성화. 물리 삭제는 하지 않는다 (REQ-CUST-003)."""
    customer = get_customer(db, customer_id)
    before = change_log_service.snapshot(customer)
    customer.is_active = False
    change_log_service.record(
        db,
        entity_type="customer",
        entity_id=customer.id,
        action=ACTION_DEACTIVATE,
        changed_by=changed_by,
        before_data=before,
        after_data=change_log_service.snapshot(customer),
    )
    db.commit()
    logger.info("customer deactivated: id=%s", customer.id)
    return get_customer(db, customer_id, with_contacts=True)


def add_contact(
    db: Session, customer_id: int, data: ContactCreate, *, changed_by: int
) -> CustomerContact:
    customer = get_customer(db, customer_id)
    contact = CustomerContact(customer_id=customer.id, **data.model_dump())
    db.add(contact)
    db.flush()
    change_log_service.record(
        db,
        entity_type="customer",
        entity_id=customer.id,
        action=ACTION_UPDATE,
        changed_by=changed_by,
        after_data={"contact_added": change_log_service.snapshot(contact)},
    )
    db.commit()
    db.refresh(contact)
    return contact


def update_contact(
    db: Session, customer_id: int, contact_id: int, data: ContactUpdate, *, changed_by: int
) -> CustomerContact:
    contact = db.scalar(
        select(CustomerContact).where(
            CustomerContact.id == contact_id,
            CustomerContact.customer_id == customer_id,
        )
    )
    if not contact:
        raise NotFoundError("담당자를 찾을 수 없습니다.")
    before = change_log_service.snapshot(contact)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)
    change_log_service.record(
        db,
        entity_type="customer",
        entity_id=customer_id,
        action=ACTION_UPDATE,
        changed_by=changed_by,
        before_data={"contact": before},
        after_data={"contact": change_log_service.snapshot(contact)},
    )
    db.commit()
    db.refresh(contact)
    return contact
