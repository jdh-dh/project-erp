from datetime import date

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PKMixin, TimestampMixin

ISSUE_TYPES = ("BUG", "IMPROVEMENT", "CUSTOMER_REQUEST", "FAILURE")
ISSUE_SEVERITIES = ("LOW", "MEDIUM", "HIGH", "CRITICAL")

ISSUE_STATUS_OPEN = "OPEN"
ISSUE_STATUS_IN_PROGRESS = "IN_PROGRESS"
ISSUE_STATUS_RESOLVED = "RESOLVED"
ISSUE_STATUS_CLOSED = "CLOSED"

# 상태 전이 규칙 (api.md 6.9절)
ISSUE_STATUS_TRANSITIONS: dict[str, tuple[str, ...]] = {
    ISSUE_STATUS_OPEN: (ISSUE_STATUS_IN_PROGRESS, ISSUE_STATUS_RESOLVED, ISSUE_STATUS_CLOSED),
    ISSUE_STATUS_IN_PROGRESS: (ISSUE_STATUS_OPEN, ISSUE_STATUS_RESOLVED, ISSUE_STATUS_CLOSED),
    ISSUE_STATUS_RESOLVED: (ISSUE_STATUS_OPEN, ISSUE_STATUS_CLOSED),
    ISSUE_STATUS_CLOSED: (),
}


class Issue(Base, PKMixin, TimestampMixin):
    __tablename__ = "issues"

    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id"), nullable=False, index=True
    )
    issue_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=ISSUE_STATUS_OPEN)
    reporter_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    assignee_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), index=True
    )
    cause_analysis: Mapped[str | None] = mapped_column(Text)
    resolution: Mapped[str | None] = mapped_column(Text)
    resolved_date: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    reporter = relationship("User", foreign_keys=[reporter_id])
    assignee = relationship("User", foreign_keys=[assignee_id])
