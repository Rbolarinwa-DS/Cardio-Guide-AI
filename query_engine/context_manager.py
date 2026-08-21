from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ConversationTurn:
    question: str
    answer: str
    topic: Optional[str] = None


@dataclass
class UserContext:
    knowledge_level: Optional[str] = None
    user_goal: Optional[str] = None
    condition: Optional[str] = None
    interest: Optional[str] = None


class ContextManager:

    def __init__(self):
        self.history: List[ConversationTurn] = []
        self.user_context = UserContext()

    def add_turn(
        self,
        question: str,
        answer: str,
        topic: Optional[str] = None
    ):
        self.history.append(
            ConversationTurn(
                question=question,
                answer=answer,
                topic=topic
            )
        )

    def update_user_context(
        self,
        knowledge_level: Optional[str] = None,
        user_goal: Optional[str] = None,
        condition: Optional[str] = None,
        interest: Optional[str] = None
    ):
        if knowledge_level:
            self.user_context.knowledge_level = knowledge_level

        if user_goal:
            self.user_context.user_goal = user_goal

        if condition:
            self.user_context.condition = condition

        if interest:
            self.user_context.interest = interest

    def get_last_turn(self) -> Optional[ConversationTurn]:
        if not self.history:
            return None

        return self.history[-1]

    def get_active_topic(self) -> Optional[str]:
        last_turn = self.get_last_turn()

        if last_turn:
            return last_turn.topic

        return self.user_context.condition or self.user_context.interest
    