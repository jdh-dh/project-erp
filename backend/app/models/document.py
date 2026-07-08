from sqlalchemy import BigInteger, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PKMixin, TimestampMixin

DOC_TYPES = (
    "REQUIREMENTS",
    "DESIGN",
    "INTERFACE",
    "TEST_PLAN",
    "VERIFICATION",
    "RELEASE_NOTE",
    "OTHER",
)


class Document(Base, PKMixin, TimestampMixin):
    __tablename__ = "documents"

    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id"), nullable=False, index=True
    )
    doc_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0")
    file_url: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    author_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    author = relationship("User")
