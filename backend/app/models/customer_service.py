"""Customer service models: CSSession, CSMessage and Ticket."""

import uuid
from enum import StrEnum

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class CSSessionStatus(StrEnum):
    ACTIVE = "active"
    CLOSED = "closed"
    ESCALATED = "escalated"


class CSSession(Base):
    """Customer service chat session model."""

    __tablename__ = "cs_sessions"

    tiktok_conversation_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True
    )
    buyer_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    buyer_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default=CSSessionStatus.ACTIVE, nullable=False, index=True
    )
    assigned_agent: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    ai_resolved: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationships
    messages: Mapped[list["CSMessage"]] = relationship(
        "CSMessage", back_populates="session", cascade="all, delete-orphan"
    )
    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket", back_populates="session", cascade="all, delete-orphan"
    )


class CSMessageRole(StrEnum):
    BUYER = "buyer"
    AI = "ai"
    AGENT = "agent"


class CSMessage(Base):
    """Customer service message model."""

    __tablename__ = "cs_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cs_sessions.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    session: Mapped["CSSession"] = relationship("CSSession", back_populates="messages")


class TicketStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Ticket(Base):
    """Support ticket (escalated from CS session) model."""

    __tablename__ = "tickets"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cs_sessions.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default=TicketStatus.OPEN, nullable=False, index=True
    )
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    session: Mapped["CSSession"] = relationship("CSSession", back_populates="tickets")
