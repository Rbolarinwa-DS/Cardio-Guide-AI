from dataclasses import dataclass
from typing import List, Optional
import re


@dataclass
class AmbiguityResult:
    ambiguous: bool
    term: Optional[str]
    possible_meanings: List[str]
    clarification_question: Optional[str]


class AmbiguityDetector:
    """
    Detect genuinely ambiguous cardiovascular terminology.

    This detector is intentionally context-aware.

    Example:

        "I've been having pressure lately."

    -> ambiguous

    But:

        "I have heavy pressure in the middle of my chest."

    -> NOT ambiguous

    because the surrounding context identifies "pressure" as
    chest pressure.

    Emergency classification should still run before ambiguity
    handling in the decision pipeline.
    """

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
        if not isinstance(question, str):
            raise TypeError("Question must be a string.")

        text = question.lower().strip()

        if not text:
            return self._not_ambiguous()

        # ----------------------------------------------------
        # Pressure
        # ----------------------------------------------------

        if self._contains_standalone_term(text, "pressure"):

            if self._pressure_has_clear_context(text):
                return self._not_ambiguous()

            return self._build_result(
                term="pressure",
                meanings=self.AMBIGUOUS_TERMS["pressure"],
            )

        # ----------------------------------------------------
        # Attack
        # ----------------------------------------------------

        if self._contains_standalone_term(text, "attack"):

            if self._attack_has_clear_context(text):
                return self._not_ambiguous()

            return self._build_result(
                term="attack",
                meanings=self.AMBIGUOUS_TERMS["attack"],
            )

        # ----------------------------------------------------
        # Failure
        # ----------------------------------------------------

        if self._contains_standalone_term(text, "failure"):

            if self._failure_has_clear_context(text):
                return self._not_ambiguous()

            return self._build_result(
                term="failure",
                meanings=self.AMBIGUOUS_TERMS["failure"],
            )

        return self._not_ambiguous()

    # ========================================================
    # CONTEXT CHECKS
    # ========================================================

    @staticmethod
    def _pressure_has_clear_context(text: str) -> bool:
        blood_pressure_patterns = [
            r"\bblood pressure\b",
            r"\bhigh blood pressure\b",
            r"\blow blood pressure\b",
            r"\bpressure reading\b",
            r"\bpressure was \d+",
            r"\bpressure is \d+",
            r"\bbp\b",
            r"\bhypertension\b",
        ]

        chest_pressure_patterns = [
            r"\bchest pressure\b",
            r"\bpressure\b.{0,40}\bchest\b",
            r"\bchest\b.{0,40}\bpressure\b",
            r"\bpressure\b.{0,40}\bheart\b",
            r"\bpressure\b.{0,40}\bbreastbone\b",
            r"\bpressure\b.{0,40}\bmiddle of (?:my|the|his|her)\s+chest\b",
        ]

        stress_patterns = [
            r"\bstress\b",
            r"\banxiety\b",
            r"\banxious\b",
            r"\bemotional\b",
            r"\bpanic\b",
            r"\bworried\b",
            r"\boverwhelmed\b",
        ]

        return (
            any(
                re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                )
                for pattern in blood_pressure_patterns
            )
            or any(
                re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                )
                for pattern in chest_pressure_patterns
            )
            or any(
                re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                )
                for pattern in stress_patterns
            )
        )

    @staticmethod
    def _attack_has_clear_context(text: str) -> bool:
        patterns = [
            r"\bheart attack\b",
            r"\bmyocardial infarction\b",
            r"\bpanic attack\b",
            r"\bpanic\b",
            r"\banxiety attack\b",
            r"\bchest pain\b.{0,40}\battack\b",
            r"\bchest pressure\b.{0,40}\battack\b",
        ]

        return any(
            re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
            for pattern in patterns
        )

    @staticmethod
    def _failure_has_clear_context(text: str) -> bool:
        patterns = [
            r"\bheart failure\b",
            r"\bcongestive heart failure\b",
            r"\btreatment failure\b",
            r"\bmedication failure\b",
            r"\btherapy failure\b",
            r"\btreatment\b.{0,30}\bfailure\b",
        ]

        return any(
            re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
            for pattern in patterns
        )

    # ========================================================
    # HELPERS
    # ========================================================

    def _build_result(
        self,
        term: str,
        meanings: List[str],
    ) -> AmbiguityResult:

        if len(meanings) == 1:
            question = (
                f"When you say '{term}', "
                f"do you mean {meanings[0]}?"
            )

        elif len(meanings) == 2:
            question = (
                f"When you say '{term}', "
                f"do you mean {meanings[0]} "
                f"or {meanings[1]}?"
            )

        else:
            question = (
                f"When you say '{term}', "
                f"do you mean "
                f"{', '.join(meanings[:-1])}, "
                f"or {meanings[-1]}?"
            )

        return AmbiguityResult(
            ambiguous=True,
            term=term,
            possible_meanings=meanings,
            clarification_question=question,
        )

    @staticmethod
    def _contains_standalone_term(
        text: str,
        term: str,
    ) -> bool:

        return bool(
            re.search(
                rf"\b{re.escape(term)}\b",
                text,
                flags=re.IGNORECASE,
            )
        )

    @staticmethod
    def _not_ambiguous() -> AmbiguityResult:
        return AmbiguityResult(
            ambiguous=False,
            term=None,
            possible_meanings=[],
            clarification_question=None,
        )