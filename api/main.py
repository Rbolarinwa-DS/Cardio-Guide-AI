import traceback
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from sqlalchemy import select

from api.schemas import ChatRequest, ChatResponse
from database.connection import SessionLocal
from database.crud import (
    create_message,
    get_conversation_messages,
    get_or_create_conversation,
    get_or_create_user,
)
from database.models import Conversation
from query_engine.cardio_guide import CardioGuide

app = FastAPI(
    title="CardioGuide AI",
    description="Evidence-based cardiovascular health education assistant.",
    version="1.0.0",
)

# ------------------------------------------------------------
# CardioGuide engine
# ------------------------------------------------------------

cardio_guide = CardioGuide("data/cardioguide_queries.csv")


# ------------------------------------------------------------
# Health / root endpoints
# ------------------------------------------------------------


@app.get("/")
def root():
    return {
        "name": "CardioGuide AI",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "CardioGuide AI",
    }


# ------------------------------------------------------------
# Chat endpoint
# ------------------------------------------------------------


@app.post(
    "/chat",
    response_model=ChatResponse,
)
def chat(request: ChatRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail=(
                "Please provide a cardiovascular "
                "health question."
            ),
        )

    user_id = (
        request.user_id
        or f"user-{uuid4().hex}"
    )

    conversation_id = (
        request.conversation_id
        or f"conversation-{uuid4().hex}"
    )

    db = SessionLocal()

    try:
        # ----------------------------------------------------
        # User
        # ----------------------------------------------------

        get_or_create_user(
            db=db,
            user_id=user_id,
        )

        # ----------------------------------------------------
        # Conversation
        # ----------------------------------------------------

        get_or_create_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
        )

        # ----------------------------------------------------
        # Existing conversation history
        #
        # The history is currently persisted and available
        # through the conversation API. Context-aware
        # generation can be connected to CardioGuide separately.
        # ----------------------------------------------------

        get_conversation_messages(
            db=db,
            conversation_id=conversation_id,
        )

        # ----------------------------------------------------
        # Persist user message
        # ----------------------------------------------------

        create_message(
            db=db,
            conversation_id=conversation_id,
            role="user",
            content=question,
        )

        # ----------------------------------------------------
        # Generate CardioGuide response
        # ----------------------------------------------------

        result = cardio_guide.ask(question)

        answer = (
            result.get("answer")
            or result.get("response")
        )

        # ----------------------------------------------------
        # Persist assistant response
        # ----------------------------------------------------

        if answer:
            create_message(
                db=db,
                conversation_id=conversation_id,
                role="assistant",
                content=answer,
            )

        # ----------------------------------------------------
        # PUBLIC API BOUNDARY
        #
        # Only expose fields intended for the frontend.
        #
        # Internal research objects, retrieval metadata,
        # response-planning information, prompts, and other
        # implementation details must remain internal.
        # ----------------------------------------------------

        public_result = {
            "action": result.get(
                "action",
                "proceed",
            ),
            "message": result.get(
                "message"
            ),
            "answer": answer,
            "flashcards": result.get(
                "flashcards",
                [],
            ),
            "visual_support": result.get(
                "visual_support"
            ),
            "sources": _serialize_sources(
                result.get(
                    "sources",
                    [],
                )
            ),
            "safety_note": result.get(
                "safety_note"
            ),
            "conversation_id": conversation_id,
            "user_id": user_id,
        }

        return ChatResponse(
            **public_result
        )

    except HTTPException:
        raise

    except Exception as exc:
        db.rollback()

        print(
            "\n[CardioGuide ERROR]"
            f"\nType: {type(exc).__name__}"
            f"\nMessage: {exc}"
        )

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=(
                "CardioGuide encountered an internal "
                "error while processing your question."
            ),
        ) from exc

    finally:
        db.close()


# ------------------------------------------------------------
# Source serialization
# ------------------------------------------------------------


def _serialize_sources(sources):
    """
    Convert internal source metadata objects into plain
    dictionaries suitable for the public API.

    Supports:

    1. Dataclass/object-based source metadata.
    2. Dictionaries for backward compatibility.

    Internal source objects should never be exposed directly
    through the FastAPI response.
    """

    serialized = []

    for source in sources or []:

        if source is None:
            continue

        # ----------------------------------------------------
        # Dictionary source
        # ----------------------------------------------------

        if isinstance(source, dict):
            serialized.append(
                {
                    "title": str(
                        source.get(
                            "title",
                            "",
                        )
                        or ""
                    ),
                    "url": str(
                        source.get(
                            "url",
                            "",
                        )
                        or ""
                    ),
                    "domain": str(
                        source.get(
                            "domain",
                            "",
                        )
                        or ""
                    ),
                    "angle": str(
                        source.get(
                            "angle",
                            "",
                        )
                        or ""
                    ),
                    "query": str(
                        source.get(
                            "query",
                            "",
                        )
                        or ""
                    ),
                }
            )

            continue

        # ----------------------------------------------------
        # Object / dataclass source
        # ----------------------------------------------------

        serialized.append(
            {
                "title": str(
                    getattr(
                        source,
                        "title",
                        "",
                    )
                    or ""
                ),
                "url": str(
                    getattr(
                        source,
                        "url",
                        "",
                    )
                    or ""
                ),
                "domain": str(
                    getattr(
                        source,
                        "domain",
                        "",
                    )
                    or ""
                ),
                "angle": str(
                    getattr(
                        source,
                        "angle",
                        "",
                    )
                    or ""
                ),
                "query": str(
                    getattr(
                        source,
                        "query",
                        "",
                    )
                    or ""
                ),
            }
        )

    return serialized


# ------------------------------------------------------------
# Conversation history
# ------------------------------------------------------------


@app.get("/conversations/{conversation_id}")
def get_conversation_history(
    conversation_id: str,
):
    db = SessionLocal()

    try:
        messages = get_conversation_messages(
            db=db,
            conversation_id=conversation_id,
        )

        return {
            "conversation_id": conversation_id,
            "messages": [
                {
                    "id": message.id,
                    "role": message.role,
                    "content": message.content,
                    "created_at": message.created_at,
                }
                for message in messages
            ],
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve conversation.",
        ) from exc

    finally:
        db.close()


# ------------------------------------------------------------
# User conversations
# ------------------------------------------------------------


@app.get("/users/{user_id}/conversations")
def get_user_conversations(
    user_id: str,
):
    db = SessionLocal()

    try:
        statement = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )

        conversations = db.scalars(statement).all()

        return {
            "user_id": user_id,
            "conversations": [
                {
                    "id": conversation.id,
                    "title": conversation.title,
                    "created_at": conversation.created_at,
                    "updated_at": conversation.updated_at,
                }
                for conversation in conversations
            ],
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve conversations.",
        ) from exc

    finally:
        db.close()