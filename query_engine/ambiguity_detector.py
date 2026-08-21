from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AmbiguityResult:
    ambiguous: bool
    term: Optional[str]
    possible_meanings: List[str]
    clarification_question: Optional[str]


class AmbiguityDetector:

    AMBIGUOUS_TERMS = {
        "pressure": [
            "blood pressure",
            "chest pressure",
            "emotional stress",
        ],
        "attack": [
            "heart attack",
            "panic attack",
        ],
        "failure": [
            "heart failure",
            "treatment failure",
        ],
    }

    def detect(self, question: str) -> AmbiguityResult:
        text = question.lower().strip()

        # Specific medical phrases remove ambiguity.
        specific_phrases = [
            "blood pressure",
            "chest pressure",
            "heart attack",
            "panic attack",
            "heart failure",
            "treatment failure",
        ]

        for phrase in specific_phrases:
            if phrase in text:
                return self._not_ambiguous()

        # Check genuinely ambiguous standalone terms.
        for term, meanings in self.AMBIGUOUS_TERMS.items():

            if self._contains_standalone_term(text, term):

                return AmbiguityResult(
                    ambiguous=True,
                    term=term,
                    possible_meanings=meanings,
                    clarification_question=(
                        f"When you say '{term}', "
                        f"do you mean "
                        f"{', '.join(meanings[:-1])}, "
                        f"or {meanings[-1]}?"
                    ),
                )

        return self._not_ambiguous()

    def _contains_standalone_term(
        self,
        text: str,
        term: str
    ) -> bool:
        words = text.replace("?", "").replace(",", "").split()

        return term in words

    def _not_ambiguous(self) -> AmbiguityResult:
        return AmbiguityResult(
            ambiguous=False,
            term=None,
            possible_meanings=[],
            clarification_question=None,
        )