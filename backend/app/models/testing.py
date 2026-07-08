from datetime import date

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PKMixin, TimestampMixin

TEST_TYPES = ("UNIT", "INTEGRATION", "FIELD")
TEST_RESULTS = ("PASS", "FAIL", "BLOCKED")


class TestCase(Base, PKMixin, TimestampMixin):
    __tablename__ = "test_cases"

    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id"), nullable=False, index=True
    )
    test_type: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    expected_result: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    runs: Mapped[list["TestRun"]] = relationship(
        back_populates="test_case", cascade="all, delete-orphan"
    )

    @property
    def last_result(self) -> str | None:
        """가장 최근 실행 결과 (REQ-TEST-004)."""
        if not self.runs:
            return None
        return max(self.runs, key=lambda r: r.id).result


class TestRun(Base, PKMixin, TimestampMixin):
    __tablename__ = "test_runs"

    test_case_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("test_cases.id"), nullable=False, index=True
    )
    run_date: Mapped[date] = mapped_column(Date, nullable=False)
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    tester_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)

    test_case: Mapped[TestCase] = relationship(back_populates="runs")
    tester = relationship("User")
