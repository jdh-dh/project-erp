from datetime import date

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PKMixin, TimestampMixin

BOARD_STATUSES = ("DESIGN", "PROTOTYPE", "PRODUCTION", "OBSOLETE")
FAB_RESULTS = ("OK", "NG", "PARTIAL")


class HwBoard(Base, PKMixin, TimestampMixin):
    __tablename__ = "hw_boards"
    __table_args__ = (
        UniqueConstraint("project_id", "name", "revision", name="uq_board_name_rev"),
    )

    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    revision: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DESIGN")
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    bom_items: Mapped[list["BomItem"]] = relationship(
        back_populates="board", cascade="all, delete-orphan"
    )
    fabrications: Mapped[list["HwFabrication"]] = relationship(
        back_populates="board", cascade="all, delete-orphan"
    )


class BomItem(Base, PKMixin, TimestampMixin):
    __tablename__ = "bom_items"

    board_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("hw_boards.id"), nullable=False, index=True
    )
    part_name: Mapped[str] = mapped_column(String(200), nullable=False)
    part_number: Mapped[str | None] = mapped_column(String(100))
    manufacturer: Mapped[str | None] = mapped_column(String(100))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    reference: Mapped[str | None] = mapped_column(String(100))
    note: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    board: Mapped[HwBoard] = relationship(back_populates="bom_items")


class HwFabrication(Base, PKMixin, TimestampMixin):
    __tablename__ = "hw_fabrications"

    board_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("hw_boards.id"), nullable=False, index=True
    )
    fab_date: Mapped[date] = mapped_column(Date, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    vendor: Mapped[str | None] = mapped_column(String(200))
    result: Mapped[str] = mapped_column(String(20), nullable=False, default="OK")
    note: Mapped[str | None] = mapped_column(Text)

    board: Mapped[HwBoard] = relationship(back_populates="fabrications")
