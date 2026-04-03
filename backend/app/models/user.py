"""User and Role models with RBAC support."""

import uuid
from enum import StrEnum

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserRole(StrEnum):
    """System role enum."""
    ADMIN = "admin"
    OPERATOR = "operator"
    CS_AGENT = "cs_agent"
    FINANCE = "finance"


class User(Base):
    """User account model."""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default=UserRole.OPERATOR)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Note: role field is just a string, not a foreign key relationship
    # role_rel relationship removed to avoid FK issues

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class Role(Base):
    """Role definition model for RBAC."""

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    permissions: Mapped[str | None] = mapped_column(Text, nullable=True)

    # No direct relationship to users since User.role is a string field
    # Users are linked by role name, not by foreign key

    def __repr__(self) -> str:
        return f"<Role {self.name}>"
