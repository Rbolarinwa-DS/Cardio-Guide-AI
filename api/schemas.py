from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """
    Request body for a CardioGuide conversation.
    """

    question: str = Field(
        ...,
        min_length=1,
        description=(
            "The user's cardiovascular health question."
        ),
    )

    user_id: Optional[str] = Field(
        default=None,
        description=(
            "Optional identifier for the user."
        ),
    )

    conversation_id: Optional[str] = Field(
        default=None,
        description=(
            "Optional identifier for the conversation."
        ),
    )


class SourceResponse(BaseModel):
    """
    Public representation of a medical source.
    """

    title: str
    url: str
    domain: str
    angle: str
    query: str


class FlashcardResponse(BaseModel):
    """
    CardioGuide learning flashcard.
    """

    angle: str
    question: str
    answer: str


class VisualSupportResponse(BaseModel):
    """
    Metadata describing recommended visual support.
    """

    recommended: bool
    angle: Optional[str] = None
    reason: Optional[str] = None


class ChatResponse(BaseModel):
    """
    Public CardioGuide chat response.

    Internal classifier metadata, evidence structures,
    implementation details, prompts, and model configuration
    are intentionally excluded from the public API.
    """

    action: str

    message: Optional[str] = None

    answer: Optional[str] = None

    flashcards: List[FlashcardResponse] = Field(
        default_factory=list
    )

    visual_support: Optional[
        VisualSupportResponse
    ] = None

    sources: List[SourceResponse] = Field(
        default_factory=list
    )

    safety_note: Optional[str] = None

    conversation_id: Optional[str] = None

    user_id: Optional[str] = None