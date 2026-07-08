from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PKMixin, TimestampMixin

MODULE_TYPES = ("FIRMWARE", "APP", "SERVER", "LIBRARY")
VERSION_STATUSES = ("DEVELOP", "RELEASED", "DEPRECATED")
BUILD_RESULTS = ("SUCCESS", "FAIL")
DEPLOY_ENVIRONMENTS = ("DEV", "STAGE", "PROD", "FIELD")


class SwModule(Base, PKMixin, TimestampMixin):
    __tablename__ = "sw_modules"
    __table_args__ = (UniqueConstraint("project_id", "name", name="uq_module_name"),)

    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    module_type: Mapped[str] = mapped_column(String(20), nullable=False)
    repo_url: Mapped[str | None] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    versions: Mapped[list["SwVersion"]] = relationship(
        back_populates="module", cascade="all, delete-orphan"
    )


class SwVersion(Base, PKMixin, TimestampMixin):
    __tablename__ = "sw_versions"
    __table_args__ = (UniqueConstraint("module_id", "version", name="uq_module_version"),)

    module_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sw_modules.id"), nullable=False, index=True
    )
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DEVELOP")
    released_date: Mapped[date | None] = mapped_column(Date)
    note: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    module: Mapped[SwModule] = relationship(back_populates="versions")
    builds: Mapped[list["SwBuild"]] = relationship(
        back_populates="version_ref", cascade="all, delete-orphan"
    )
    deployments: Mapped[list["SwDeployment"]] = relationship(
        back_populates="version_ref", cascade="all, delete-orphan"
    )


class SwBuild(Base, PKMixin):
    __tablename__ = "sw_builds"

    version_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sw_versions.id"), nullable=False, index=True
    )
    build_no: Mapped[str] = mapped_column(String(50), nullable=False)
    commit_hash: Mapped[str | None] = mapped_column(String(64))
    built_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    result: Mapped[str] = mapped_column(String(20), nullable=False, default="SUCCESS")
    note: Mapped[str | None] = mapped_column(Text)

    version_ref: Mapped[SwVersion] = relationship(back_populates="builds")


class SwDeployment(Base, PKMixin):
    __tablename__ = "sw_deployments"

    version_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sw_versions.id"), nullable=False, index=True
    )
    environment: Mapped[str] = mapped_column(String(20), nullable=False)
    deployed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    note: Mapped[str | None] = mapped_column(Text)

    version_ref: Mapped[SwVersion] = relationship(back_populates="deployments")
