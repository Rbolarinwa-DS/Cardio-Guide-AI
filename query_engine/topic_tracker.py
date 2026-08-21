from dataclasses import dataclass
from typing import Optional

from query_engine.context_manager import ContextManager


@dataclass
class TopicDecision:
    topic: Optional[str]
    switched: bool


class TopicTracker:

    def __init__(self, context: ContextManager):
        self.context = context

    def detect(self, question: str, detected_topic: Optional[str]) -> TopicDecision:
        active_topic = self.context.get_active_topic()

        if detected_topic:
            switched = (
                active_topic is not None
                and detected_topic.lower() != active_topic.lower()
            )

            return TopicDecision(
                topic=detected_topic,
                switched=switched
            )

        return TopicDecision(
            topic=active_topic,
            switched=False
        )

    def update(self, topic: Optional[str]):
        if topic:
            self.context.user_context.condition = topic