from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import (
    Conversation,
    Message,
    User,
    UserProfile,
)


def get_user(
    db: Session,
    user_id: str,
) -> Optional[User]:
    """Retrieve a user by ID."""

    return db.get(User, user_id)


def create_user(
    db: Session,
    user_id: str,
) -> User:
    """Create a new user."""

    user = User(id=user_id)

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_or_create_user(
    db: Session,
    user_id: str,
) -> User:
    """Return an existing user or create one."""

    user = get_user(db, user_id)

    if user is not None:
        return user

    return create_user(db, user_id)


def get_conversation(
    db: Session,
    conversation_id: str,
) -> Optional[Conversation]:
    """Retrieve a conversation with its messages."""

    statement = (
        select(Conversation)
        .where(Conversation.id == conversation_id)
    )

    return db.scalars(statement).first()


def create_conversation(
    db: Session,
    conversation_id: str,
    user_id: str,
    title: Optional[str] = None,
) -> Conversation:
    """Create a conversation."""

    conversation = Conversation(
        id=conversation_id,
        user_id=user_id,
        title=title,
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


def get_or_create_conversation(
    db: Session,
    conversation_id: str,
    user_id: str,
    title: Optional[str] = None,
) -> Conversation:
    """Return an existing conversation or create one."""

    conversation = get_conversation(
        db,
        conversation_id,
    )

    if conversation is not None:
        return conversation

    return create_conversation(
        db,
        conversation_id,
        user_id,
        title,
    )


def create_message(
    db: Session,
    conversation_id: str,
    role: str,
    content: str,
) -> Message:
    """Store a conversation message."""

    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message


def get_conversation_messages(
    db: Session,
    conversation_id: str,
) -> list[Message]:
    """Retrieve messages in chronological order."""

    statement = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )

    return list(db.scalars(statement).all())


def get_user_profile(
    db: Session,
    user_id: str,
) -> Optional[UserProfile]:
    """Retrieve a user's profile."""

    statement = (
        select(UserProfile)
        .where(UserProfile.user_id == user_id)
    )

    return db.scalars(statement).first()


def create_or_update_profile(
    db: Session,
    user_id: str,
    goal: Optional[str] = None,
    preferred_explanation_level: Optional[str] = None,
) -> UserProfile:
    """Create or update a user's personalization profile."""

    profile = get_user_profile(db, user_id)

    if profile is None:
        profile = UserProfile(
            user_id=user_id,
            goal=goal,
            preferred_explanation_level=preferred_explanation_level,
        )

        db.add(profile)

    else:
        if goal is not None:
            profile.goal = goal

        if preferred_explanation_level is not None:
            profile.preferred_explanation_level = (
                preferred_explanation_level
            )

    db.commit()
    db.refresh(profile)

    return profile