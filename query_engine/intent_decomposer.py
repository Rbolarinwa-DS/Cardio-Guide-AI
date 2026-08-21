from dataclasses import dataclass
from typing import List


@dataclass
class SubQuestion:
    question: str
    position: int


class IntentDecomposer:

    def decompose(self, question: str) -> List[SubQuestion]:
        parts = self._split_questions(question)

        return [
            SubQuestion(
                question=part.strip(),
                position=index
            )
            for index, part in enumerate(parts, start=1)
            if part.strip()
        ]

    def _split_questions(self, question: str) -> List[str]:
        question = question.strip()

        # Handle common multi-question connectors.
        replacements = [
            ", and can",
            ", can",
            ", what",
            ", why",
            ", how",
            " and what",
            " and can",
            " and how",
            " and why",
        ]

        for replacement in replacements:
            question = question.replace(
                replacement,
                f"|{replacement.strip()}"
            )

        parts = question.split("|")

        cleaned = []

        for part in parts:
            part = part.strip(" ,")

            if part:
                cleaned.append(part)

        return cleaned