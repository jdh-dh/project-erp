from datetime import date

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, PKMixin, TimestampMixin

MS_STATUS_PENDING = "PENDING"
MS_STATUS_ACHIEVED = "ACHIEVED"


class Milestone(Base, PKMixin, TimestampMixin):
    __tablename__ = "milestones"

    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=MS_STATUS_PENDING)
    achieved_date: Mapped[date | None] = mapped_column(Date)
    note: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    @property
    def is_delayed(self) -> bool:
        """지연 판정 (REQ-MS-003): 목표일 경과 & 미달성."""
        return bool(self.due_date < date.today() and self.status == MS_STATUS_PENDING)
