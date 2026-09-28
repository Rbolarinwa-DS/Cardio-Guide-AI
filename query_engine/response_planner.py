from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from query_engine.evidence_builder import EvidencePackage
from query_engine.schemas import QueryAnalysis


@dataclass
class ResponsePlan:
    """
    Structured instructions for the response-generation stage.

    The planner decides WHAT evidence should be used.
    The response generator decides HOW that evidence should be
    expressed to the user.
    """

    primary_angles: List[str]
    supporting_angles: List[str]

    response_style: str

    include_sources: bool
    include_safety_note: bool

    generate_flashcards: bool
    flashcard_angles: List[str]

    recommend_visual: bool
    visual_angle: Optional[str]


class ResponsePlanner:
    """
    Converts QueryAnalysis + EvidencePackage into a constrained
    response-generation plan.

    The planner deliberately avoids generating medical content.
    Its responsibility is evidence selection and response policy.
    """

    # ============================================================
    # INTENT → EVIDENCE RULES
    # ============================================================

    ANGLE_RULES: Dict[str, Dict[str, List[str]]] = {
        "definition": {
            "primary": [
                "definition",
            ],
            "supporting": [
                "types",
                "complications",
            ],
        },

        "symptoms": {
            "primary": [
                "symptoms",
            ],
            "supporting": [
                "when to seek medical care",
                "complications",
            ],
        },

        "risk_factors": {
            "primary": [
                "risk factors",
            ],
            "supporting": [
                "causes",
                "prevention",
                "lifestyle",
            ],
        },

        "causes": {
            "primary": [
                "causes",
            ],
            "supporting": [
                "risk factors",
                "types",
            ],
        },

        "treatment": {
            "primary": [
                "management and treatment",
            ],
            "supporting": [
                "lifestyle",
                "monitoring",
            ],
        },

        "side_effects": {
            "primary": [
                "management and treatment",
            ],
            "supporting": [
                "monitoring",
            ],
        },

        "comparison": {
            "primary": [
                "definition",
            ],
            "supporting": [
                "types",
                "monitoring",
            ],
        },

        "diagnosis": {
            "primary": [
                "diagnosis",
            ],
            "supporting": [
                "monitoring",
                "symptoms",
            ],
        },

        "complications": {
            "primary": [
                "complications",
            ],
            "supporting": [
                "symptoms",
                "when to seek medical care",
            ],
        },

        "prevention": {
            "primary": [
                "prevention",
            ],
            "supporting": [
                "risk factors",
                "lifestyle",
            ],
        },

        "monitoring": {
            "primary": [
                "monitoring",
            ],
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

    # ============================================================
    # DEFAULT BEHAVIOR
    # ============================================================

    DEFAULT_PRIMARY = [
        "definition",
    ]

    DEFAULT_SUPPORTING = [
        "symptoms",
        "risk factors",
    ]

    # ============================================================
    # VISUAL RULES
    # ============================================================

    VISUAL_ANGLES: Dict[str, str] = {
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

    # ============================================================
    # SAFETY-SENSITIVE INTENTS
    # ============================================================

    SAFETY_INTENTS = {
        "symptoms",
        "treatment",
        "side_effects",
        "diagnosis",
        "complications",
        "prevention",
        "monitoring",
    }

    # ============================================================
    # PLAN
    # ============================================================

    def plan(
        self,
        analysis: QueryAnalysis,
        evidence: EvidencePackage,
    ) -> ResponsePlan:
        """
        Build a constrained response plan.

        Pipeline:

            QueryAnalysis
                  ↓
            intent detection
                  ↓
            angle rules
                  ↓
            evidence availability filtering
                  ↓
            response policy
                  ↓
            ResponsePlan
        """

        intent = self._normalize_intent(
            analysis.intent
        )

        rule = self.ANGLE_RULES.get(
            intent,
            {
                "primary": self.DEFAULT_PRIMARY,
                "supporting": self.DEFAULT_SUPPORTING,
            },
        )

        # --------------------------------------------------------
        # 1. Select only angles that actually contain evidence.
        # --------------------------------------------------------

        primary_angles = self._available_angles(
            rule["primary"],
            evidence,
        )

        supporting_angles = self._available_angles(
            rule["supporting"],
            evidence,
        )

        # --------------------------------------------------------
        # 2. If requested primary evidence is unavailable,
        #    use the strongest available evidence instead.
        # --------------------------------------------------------

        if not primary_angles:
            primary_angles = self._fallback_primary_angles(
                evidence=evidence,
                excluded_angles=supporting_angles,
            )

        # --------------------------------------------------------
        # 3. Remove overlap.
        # --------------------------------------------------------

        supporting_angles = [
            angle
            for angle in supporting_angles
            if angle not in primary_angles
        ]

        # --------------------------------------------------------
        # 4. Response style comes from analysis when available.
        # --------------------------------------------------------

        response_style = (
            analysis.response_strategy
            or "clear educational explanation"
        )

        # --------------------------------------------------------
        # 5. Safety policy.
        # --------------------------------------------------------

        include_safety_note = (
            intent in self.SAFETY_INTENTS
        )

        # --------------------------------------------------------
        # 6. Flashcard planning.
        # --------------------------------------------------------

        flashcard_angles = self._build_flashcard_angles(
            primary_angles=primary_angles,
            supporting_angles=supporting_angles,
            evidence=evidence,
        )

        generate_flashcards = bool(
            flashcard_angles
        )

        # --------------------------------------------------------
        # 7. Visual planning.
        # --------------------------------------------------------

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

        # --------------------------------------------------------
        # 8. Return planning decision.
        # --------------------------------------------------------

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

    # ============================================================
    # INTENT NORMALIZATION
    # ============================================================

    def _normalize_intent(
        self,
        intent: Optional[str],
    ) -> str:
        """
        Normalize analyzer output before rule lookup.
        """

        if not intent:
            return "general_information"

        normalized = (
            intent
            .strip()
            .lower()
        )

        aliases = {
            "risk factors": "risk_factors",
            "risk-factor": "risk_factors",
            "risk factor": "risk_factors",

            "general": "general_information",
            "overview": "general_information",

            "manage": "treatment",
            "management": "treatment",

            "side effect": "side_effects",
            "side-effects": "side_effects",
        }

        return aliases.get(
            normalized,
            normalized,
        )

    # ============================================================
    # AVAILABLE ANGLES
    # ============================================================

    def _available_angles(
        self,
        angles: List[str],
        evidence: EvidencePackage,
    ) -> List[str]:
        """
        Preserve the ordering defined by the planning rules,
        while removing angles with no usable evidence.

        EvidencePackage.evidence_by_angle now stores lists of
        EvidenceClaim objects rather than formatted strings.
        """

        available: List[str] = []

        for angle in angles:
            if self._has_evidence_for_angle(
                angle,
                evidence,
            ):
                available.append(angle)

        return available

    # ============================================================
    # FALLBACK ANGLES
    # ============================================================

    def _fallback_primary_angles(
        self,
        evidence: EvidencePackage,
        excluded_angles: List[str],
    ) -> List[str]:
        """
        Select available evidence when the requested primary angle
        has no evidence.

        Priority:
        1. definition
        2. other available angles in EvidenceBuilder order
        """

        candidates: List[str] = []

        if (
            "definition" not in excluded_angles
            and self._has_evidence_for_angle(
                "definition",
                evidence,
            )
        ):
            candidates.append(
                "definition"
            )

        for angle in evidence.evidence_by_angle:

            if angle in candidates:
                continue

            if angle in excluded_angles:
                continue

            if not self._has_evidence_for_angle(
                angle,
                evidence,
            ):
                continue

            candidates.append(
                angle
            )

            if len(candidates) >= 3:
                break

        return candidates

    # ============================================================
    # FLASHCARD ANGLES
    # ============================================================

    def _build_flashcard_angles(
        self,
        primary_angles: List[str],
        supporting_angles: List[str],
        evidence: EvidencePackage,
    ) -> List[str]:
        """
        Select a small deterministic set of flashcard angles.

        Primary evidence is always preferred over supporting evidence.
        """

        candidates = (
            primary_angles[:2]
            + supporting_angles[:2]
        )

        selected: List[str] = []

        for angle in candidates:

            if angle in selected:
                continue

            if not self._has_evidence_for_angle(
                angle,
                evidence,
            ):
                continue

            selected.append(
                angle
            )

            if len(selected) >= 2:
                break

        return selected

    # ============================================================
    # EVIDENCE VALIDATION
    # ============================================================

    def _has_evidence(
        self,
        content,
    ) -> bool:
        """
        Determine whether an evidence collection contains
        usable evidence.

        The current EvidencePackage stores evidence as a list of
        EvidenceClaim objects. This method therefore validates
        collections rather than calling string methods directly.
        """

        if not content:
            return False

        # New EvidencePackage format:
        # List[EvidenceClaim]
        if isinstance(content, list):
            for claim in content:
                if claim is None:
                    continue

                text = getattr(
                    claim,
                    "text",
                    "",
                )

                if not isinstance(text, str):
                    continue

                normalized = (
                    text
                    .strip()
                    .lower()
                )

                if normalized:
                    return True

            return False

        # Backward compatibility for any remaining callers that
        # may still provide a plain evidence string.
        if isinstance(content, str):
            normalized = (
                content
                .strip()
                .lower()
            )

            if not normalized:
                return False

            if normalized == (
                "no evidence retrieved."
            ):
                return False

            if normalized == (
                "no reliable evidence was retrieved "
                "from the approved medical sources."
            ):
                return False

            return True

        return False

    def _has_evidence_for_angle(
        self,
        angle: str,
        evidence: EvidencePackage,
    ) -> bool:
        """
        Validate evidence for one specific angle.
        """

        content = (
            evidence.evidence_by_angle.get(
                angle,
                [],
            )
        )

        return self._has_evidence(
            content
        )