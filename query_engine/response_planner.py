from dataclasses import dataclass
from typing import List

from query_engine.evidence_builder import EvidencePackage
from query_engine.schemas import QueryAnalysis


@dataclass
class ResponsePlan:
    primary_angles: List[str]
    supporting_angles: List[str]

    response_style: str

    include_sources: bool
    include_safety_note: bool

    generate_flashcards: bool
    flashcard_angles: List[str]

    recommend_visual: bool
    visual_angle: str | None


class ResponsePlanner:

    ANGLE_RULES = {
        "definition": {
            "primary": ["definition"],
            "supporting": ["types", "complications"],
        },
        "symptoms": {
            "primary": ["symptoms"],
            "supporting": [
                "when to seek medical care",
                "complications",
            ],
        },
        "risk_factors": {
            "primary": ["risk factors"],
            "supporting": [
                "causes",
                "prevention",
                "lifestyle",
            ],
        },
        "causes": {
            "primary": ["causes"],
            "supporting": [
                "risk factors",
                "types",
            ],
        },
        "treatment": {
            "primary": ["management and treatment"],
            "supporting": [
                "lifestyle",
                "monitoring",
            ],
        },
        "side_effects": {
            "primary": ["management and treatment"],
            "supporting": [
                "monitoring",
            ],
        },
        "comparison": {
            "primary": ["definition"],
            "supporting": [
                "types",
                "monitoring",
            ],
        },
        "diagnosis": {
            "primary": ["diagnosis"],
            "supporting": [
                "monitoring",
                "symptoms",
            ],
        },
        "complications": {
            "primary": ["complications"],
            "supporting": [
                "symptoms",
                "when to seek medical care",
            ],
        },
        "prevention": {
            "primary": ["prevention"],
            "supporting": [
                "risk factors",
                "lifestyle",
            ],
        },
        "monitoring": {
            "primary": ["monitoring"],
            "supporting": [
                "diagnosis",
                "lifestyle",
            ],
        },
        "general_information": {
            "primary": [
                "definition",
                "symptoms",
                "causes",
            ],
            "supporting": [
                "risk factors",
                "prevention",
                "management and treatment",
            ],
        },
    }

    DEFAULT_PRIMARY = ["definition"]

    DEFAULT_SUPPORTING = [
        "symptoms",
        "risk factors",
    ]

    VISUAL_ANGLES = {
        "definition": "definition",
        "symptoms": "symptoms",
        "causes": "causes",
        "risk_factors": "risk factors",
        "diagnosis": "diagnosis",
        "complications": "complications",
        "prevention": "prevention",
        "treatment": "management and treatment",
        "side_effects": "management and treatment",
        "comparison": "definition",
        "monitoring": "monitoring",
        "general_information": "definition",
    }

    SAFETY_INTENTS = {
        "symptoms",
        "treatment",
        "side_effects",
        "diagnosis",
        "complications",
        "prevention",
        "monitoring",
    }

    def plan(
        self,
        analysis: QueryAnalysis,
        evidence: EvidencePackage,
    ) -> ResponsePlan:

        intent = (
            analysis.intent
            or "general_information"
        ).lower().strip()

        rule = self.ANGLE_RULES.get(
            intent,
            {
                "primary": self.DEFAULT_PRIMARY,
                "supporting": self.DEFAULT_SUPPORTING,
            },
        )

        primary_angles = self._available_angles(
            rule["primary"],
            evidence,
        )

        supporting_angles = self._available_angles(
            rule["supporting"],
            evidence,
        )

        # If the intended primary evidence is unavailable,
        # fall back to whatever evidence actually exists.
        if not primary_angles:

            available = [
                angle
                for angle in evidence.evidence_by_angle
                if self._has_evidence(
                    evidence.evidence_by_angle[angle]
                )
            ]

            primary_angles = available[:3]

        response_style = (
            analysis.response_strategy
            or "clear educational explanation"
        )

        include_safety_note = (
            intent in self.SAFETY_INTENTS
        )

        # Flashcards are useful for educational questions,
        # but should be based only on available evidence.
        flashcard_angles = (
            primary_angles[:2]
            + supporting_angles[:2]
        )

        # Remove duplicates while preserving order.
        flashcard_angles = list(
            dict.fromkeys(flashcard_angles)
        )

        generate_flashcards = bool(
            flashcard_angles
        )

        visual_angle = self.VISUAL_ANGLES.get(
            intent
        )

        recommend_visual = (
            visual_angle is not None
            and self._has_evidence_for_angle(
                visual_angle,
                evidence,
            )
        )

        return ResponsePlan(
            primary_angles=primary_angles,
            supporting_angles=supporting_angles,
            response_style=response_style,
            include_sources=True,
            include_safety_note=include_safety_note,
            generate_flashcards=generate_flashcards,
            flashcard_angles=flashcard_angles,
            recommend_visual=recommend_visual,
            visual_angle=visual_angle,
        )

    def _available_angles(
        self,
        angles: List[str],
        evidence: EvidencePackage,
    ) -> List[str]:

        available = []

        for angle in angles:

            content = evidence.evidence_by_angle.get(
                angle,
                "",
            )

            if self._has_evidence(content):
                available.append(angle)

        return available

    def _has_evidence(
        self,
        content: str,
    ) -> bool:

        return bool(
            content
            and content.strip()
            and content.strip()
            != "No evidence retrieved."
        )

    def _has_evidence_for_angle(
        self,
        angle: str,
        evidence: EvidencePackage,
    ) -> bool:

        return self._has_evidence(
            evidence.evidence_by_angle.get(
                angle,
                "",
            )
        )