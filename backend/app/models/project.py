from datetime import date

from sqlalchemy import BigInteger, Date, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PKMixin, TimestampMixin

PROJECT_TYPES = ("HW", "SW", "HYBRID")

STATUS_PLANNED = "PLANNED"
STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_ON_HOLD = "ON_HOLD"
STATUS_COMPLETED = "COMPLETED"
STATUS_CANCELED = "CANCELED"

PROJECT_STATUSES = (
    STATUS_PLANNED,
    STATUS_IN_PROGRESS,
    STATUS_ON_HOLD,
    STATUS_COMPLETED,
    STATUS_CANCELED,
)

# 상태 전이 규칙 (api.md 6절)
STATUS_TRANSITIONS: dict[str, tuple[str, ...]] = {
    STATUS_PLANNED: (STATUS_IN_PROGRESS, STATUS_CANCELED),
    STATUS_IN_PROGRESS: (STATUS_ON_HOLD, STATUS_COMPLETED, STATUS_CANCELED),
    STATUS_ON_HOLD: (STATUS_IN_PROGRESS, STATUS_CANCELED),
    STATUS_COMPLETED: (),
    STATUS_CANCELED: (),
}


class Project(Base, PKMixin, TimestampMixin):
    __tablename__ = "projects"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    customer_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("customers.id"), nullable=False, index=True
    )
    project_type: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=STATUS_PLANNED)
    manager_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(Text)

    customer = relationship("Customer")
    manager = relationship("User")
    members: Mapped[list["ProjectMember"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    contracts = relationship(
        "Contract", back_populates="project", cascade="all, delete-orphan"
    )


class ProjectMember(Base, PKMixin, TimestampMixin):
    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_member"),)

    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    role: Mapped[str | None] = mapped_column(String(50))

    project: Mapped[Project] = relationship(back_populates="members")
    user = relationship("User")
