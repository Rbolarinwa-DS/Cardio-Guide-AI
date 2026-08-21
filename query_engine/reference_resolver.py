from dataclasses import dataclass
from typing import Optional

from query_engine.context_manager import ContextManager


@dataclass
class ResolvedQuery:
    original_question: str
    resolved_question: str
    active_topic: Optional[str]
    needs_clarification: bool


class ReferenceResolver:

    FOLLOW_UP_PHRASES = {
        "why": "Why is that?",
        "how": "How does that work?",
        "explain that": "Explain that.",
        "tell me more": "Tell me more about that.",
        "give me an example": "Give me an example of that.",
    }

    def __init__(self, context: ContextManager):
        self.context = context

    def resolve(self, question: str) -> ResolvedQuery:
        question = question.strip()
        active_topic = self.context.get_active_topic()

        last_turn = self.context.get_last_turn()

        # Complete question with an identifiable topic
        if active_topic and self._is_follow_up(question):
            resolved_question = f"{question} about {active_topic}"

            return ResolvedQuery(
                original_question=question,
                resolved_question=resolved_question,
                active_topic=active_topic,
                needs_clarification=False,
            )

        # Pronoun/reference such as "it", "they", "that"
        if self._contains_reference(question):
            if active_topic:
                resolved_question = self._replace_reference(
                    question,
                    active_topic
                )

                return ResolvedQuery(
                    original_question=question,
                    resolved_question=resolved_question,
                    active_topic=active_topic,
                    needs_clarification=False,
                )

            return ResolvedQuery(
                original_question=question,
                resolved_question=question,
                active_topic=None,
                needs_clarification=True,
            )

        # Very vague question with no conversation context
        if self._is_vague(question) and not active_topic:
            return ResolvedQuery(
                original_question=question,
                resolved_question=question,
                active_topic=None,
                needs_clarification=True,
            )

        return ResolvedQuery(
            original_question=question,
            resolved_question=question,
            active_topic=active_topic,
            needs_clarification=False,
        )

    def _is_follow_up(self, question: str) -> bool:
        normalized = question.lower().strip()

        return (
            normalized in self.FOLLOW_UP_PHRASES
            or normalized.startswith("why")
            or normalized.startswith("how")
            or normalized.startswith("explain that")
            or normalized.startswith("tell me more")
            or normalized.startswith("give me an example")
        )

    def _contains_reference(self, question: str) -> bool:
        words = question.lower().split()

        references = {
            "it",
            "its",
            "they",
            "them",
            "that",
            "this",
            "these",
            "those",
        }

        return any(word.strip(".,?!") in references for word in words)

    def _is_vague(self, question: str) -> bool:
        normalized = question.lower().strip()

        vague_questions = {
            "why?",
            "how?",
            "what should i do?",
            "is it dangerous?",
            "can i take it?",
            "what about it?",
        }

        return normalized in vague_questions

    def _replace_reference(
        self,
        question: str,
        topic: str
    ) -> str:
        replacements = {
            "it": topic,
            "its": f"{topic}'s",
            "that": topic,
            "this": topic,
            "these": topic,
            "those": topic,
        }

        words = question.split()
        resolved_words = []

        for word in words:
            cleaned = word.lower().strip(".,?!")

            if cleaned in replacements:
                replacement = replacements[cleaned]

                punctuation = ""
                if word[-1:] in ".,?!":
                    punctuation = word[-1]

                resolved_words.append(replacement + punctuation)
            else:
                resolved_words.append(word)

        return " ".join(resolved_words)