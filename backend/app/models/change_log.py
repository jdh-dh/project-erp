from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PKMixin

ACTION_CREATE = "CREATE"
ACTION_UPDATE = "UPDATE"
ACTION_STATUS_CHANGE = "STATUS_CHANGE"
ACTION_DEACTIVATE = "DEACTIVATE"


class ChangeLog(Base, PKMixin):
    __tablename__ = "change_logs"
    __table_args__ = (Index("ix_change_logs_entity", "entity_type", "entity_id"),)

    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_by: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    before_data: Mapped[dict | None] = mapped_column(JSONB)
    after_data: Mapped[dict | None] = mapped_column(JSONB)

    changed_by_user = relationship("User")
