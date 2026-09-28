from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    profile: Mapped[Optional["UserProfile"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )

    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    goal: Mapped[Optional[str]] = mapped_column(Text)
    preferred_explanation_level: Mapped[Optional[str]] = mapped_column(
        String(50)
    )

    user: Mapped["User"] = relationship(
        back_populates="profile",
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    title: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    user: Mapped["User"] = relationship(
        back_populates="conversations",
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    conversation: Mapped["Conversation"] = relationship(
        back_populates="messages",
    )