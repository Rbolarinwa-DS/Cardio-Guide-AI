from dataclasses import dataclass
from typing import Optional


@dataclass
class QueryAnalysis:
    original_question: str

    topic: Optional[str] = None
    subtopic: Optional[str] = None
    intent: Optional[str] = None

    explicit_depth: Optional[str] = None
    knowledge_level: Optional[str] = None
    user_goal: Optional[str] = None

    response_strategy: Optional[str] = None
    visual_support: Optional[str] = None