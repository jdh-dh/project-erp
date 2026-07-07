from datetime import date

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PKMixin, TimestampMixin

WBS_STATUS_TODO = "TODO"
WBS_STATUS_IN_PROGRESS = "IN_PROGRESS"
WBS_STATUS_DONE = "DONE"
WBS_STATUSES = (WBS_STATUS_TODO, WBS_STATUS_IN_PROGRESS, WBS_STATUS_DONE)


class WbsItem(Base, PKMixin, TimestampMixin):
    __tablename__ = "wbs_items"

    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id"), nullable=False, index=True
    )
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("wbs_items.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    assignee_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    progress: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=WBS_STATUS_TODO)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    assignee = relationship("User")

    @property
    def is_delayed(self) -> bool:
        """지연 판정 (REQ-WBS-004): 종료일 경과 & 미완료."""
        return bool(
            self.end_date
            and self.end_date < date.today()
            and self.status != WBS_STATUS_DONE
        )
