from typing import Dict, List, Optional

from query_engine.evidence_builder import EvidencePackage
from query_engine.response_planner import ResponsePlan


class ResponseGenerator:
    """
    Generates the final user-facing CardioGuide response
    from structured evidence and a response plan.

    Responsibilities:
    - Select evidence according to the response plan.
    - Generate a concise educational answer.
    - Generate evidence-backed flashcards.
    - Recommend visual support when planned.
    - Preserve source metadata.
    - Add safety notes when required.
    """

    def generate(
        self,
        evidence: EvidencePackage,
        plan: ResponsePlan,
    ) -> Dict:
        answer = self._generate_answer(
            evidence,
            plan,
        )

        flashcards = self._generate_flashcards(
            evidence,
            plan,
        )

        visual_support = self._generate_visual_support(
            evidence,
            plan,
        )

        safety_note = self._generate_safety_note(
            plan,
        )

        sources = self._select_sources(
            evidence,
            plan,
        )

        return {
            "answer": answer,
            "flashcards": flashcards,
            "visual_support": visual_support,
            "sources": sources,
            "safety_note": safety_note,
        }

    # ==========================================================
    # ANSWER GENERATION
    # ==========================================================

    def _generate_answer(
        self,
        evidence: EvidencePackage,
        plan: ResponsePlan,
    ) -> str:

        sections = []

        for angle in plan.primary_angles:
            content = self._get_angle_evidence(
                evidence,
                angle,
            )

            if content:
                cleaned = self._clean_evidence_text(
                    content
                )

                if cleaned:
                    sections.append(cleaned)

        for angle in plan.supporting_angles:
            content = self._get_angle_evidence(
                evidence,
                angle,
            )

            if content:
                cleaned = self._clean_evidence_text(
                    content
                )

                if cleaned:
                    sections.append(cleaned)

        if not sections:
            return (
                "I could not retrieve enough reliable "
                "evidence from the approved medical sources "
                "to answer this question safely."
            )

        unique_sections = self._deduplicate_text(
            sections
        )

        return self._normalize_answer(
            " ".join(unique_sections)
        )

    # ==========================================================
    # EVIDENCE EXTRACTION
    # ==========================================================

    def _get_angle_evidence(
        self,
        evidence: EvidencePackage,
        angle: str,
    ) -> str:

        content = evidence.evidence_by_angle.get(
            angle,
            "",
        )

        if not self._has_evidence(content):
            return ""

        return content

    def _has_evidence(
        self,
        content: Optional[str],
    ) -> bool:

        if not content:
            return False

        return (
            content.strip()
            and content.strip()
            != "No evidence retrieved."
        )

    # ==========================================================
    # FLASHCARDS
    # ==========================================================

    def _generate_flashcards(
        self,
        evidence: EvidencePackage,
        plan: ResponsePlan,
    ) -> List[Dict]:

        if not plan.generate_flashcards:
            return []

        flashcards = []

        for angle in plan.flashcard_angles:

            claims = evidence.claims_by_angle.get(
                angle,
                [],
            )

            if not claims:
                continue

            # Use the first verified claim for the angle.
            claim = claims[0]

            text = str(
                claim.get(
                    "text",
                    "",
                )
            ).strip()

            if not text:
                continue

            question = self._flashcard_question(
                angle
            )

            flashcards.append(
                {
                    "angle": angle,
                    "question": question,
                    "answer": self._clean_claim_text(
                        text
                    ),
                }
            )

        return flashcards

    def _flashcard_question(
        self,
        angle: str,
    ) -> str:

        questions = {
            "definition": (
                "What is this condition?"
            ),
            "symptoms": (
                "What symptoms can this condition cause?"
            ),
            "causes": (
                "What can cause this condition?"
            ),
            "risk factors": (
                "What increases the risk of this condition?"
            ),
            "diagnosis": (
                "How is this condition diagnosed?"
            ),
            "complications": (
                "What complications can this condition cause?"
            ),
            "prevention": (
                "How can this condition be prevented?"
            ),
            "management and treatment": (
                "How is this condition managed or treated?"
            ),
            "types": (
                "What types of this condition are there?"
            ),
            "monitoring": (
                "How should this condition be monitored?"
            ),
            "lifestyle": (
                "What lifestyle factors are relevant "
                "to this condition?"
            ),
            "when to seek medical care": (
                "When should someone seek medical care?"
            ),
        }

        return questions.get(
            angle,
            f"What should you know about {angle}?",
        )

    # ==========================================================
    # VISUAL SUPPORT
    # ==========================================================

    def _generate_visual_support(
        self,
        evidence: EvidencePackage,
        plan: ResponsePlan,
    ) -> Dict:

        if not plan.recommend_visual:
            return {
                "recommended": False,
                "angle": None,
                "reason": "",
            }

        angle = plan.visual_angle

        if not angle:
            return {
                "recommended": False,
                "angle": None,
                "reason": "",
            }

        if not self._has_evidence(
            evidence.evidence_by_angle.get(
                angle,
                "",
            )
        ):
            return {
                "recommended": False,
                "angle": None,
                "reason": "",
            }

        return {
            "recommended": True,
            "angle": angle,
            "reason": (
                "A visual explanation may help the user "
                f"understand the {angle} aspect of the topic."
            ),
        }

    # ==========================================================
    # SAFETY
    # ==========================================================

    def _generate_safety_note(
        self,
        plan: ResponsePlan,
    ) -> Optional[str]:

        if not plan.include_safety_note:
            return None

        return (
            "This information is for educational purposes "
            "and does not replace advice from a qualified "
            "health professional."
        )

    # ==========================================================
    # SOURCES
    # ==========================================================

    def _select_sources(
        self,
        evidence: EvidencePackage,
        plan: ResponsePlan,
    ) -> List[Dict]:

        if not plan.include_sources:
            return []

        relevant_angles = set(
            plan.primary_angles
            + plan.supporting_angles
        )

        selected = []

        for source in evidence.sources:

            angle = source.get(
                "angle",
                "",
            )

            if (
                relevant_angles
                and angle not in relevant_angles
            ):
                continue

            selected.append(source)

        if not selected:
            selected = list(
                evidence.sources
            )

        return self._remove_duplicate_sources(
            selected
        )

    # ==========================================================
    # TEXT CLEANING
    # ==========================================================

    def _clean_evidence_text(
        self,
        content: str,
    ) -> str:

        if not content:
            return ""

        lines = content.splitlines()

        cleaned_lines = []

        for line in lines:

            line = line.strip()

            if not line:
                continue

            # Remove internal source markers.
            if (
                line.startswith("[")
                and line.endswith("]")
            ):
                continue

            cleaned_lines.append(line)

        return " ".join(
            cleaned_lines
        ).strip()

    def _clean_claim_text(
        self,
        text: str,
    ) -> str:

        if not text:
            return ""

        return " ".join(
            text.split()
        ).strip()

    def _normalize_answer(
        self,
        answer: str,
    ) -> str:

        if not answer:
            return ""

        return " ".join(
            answer.split()
        ).strip()

    # ==========================================================
    # DUPLICATION CONTROL
    # ==========================================================

    def _deduplicate_text(
        self,
        sections: List[str],
    ) -> List[str]:

        unique = []
        seen = set()

        for section in sections:

            normalized = (
                section
                .strip()
                .lower()
            )

            if not normalized:
                continue

            if normalized in seen:
                continue

            seen.add(normalized)
            unique.append(
                section.strip()
            )

        return unique

    def _remove_duplicate_sources(
        self,
        sources: List[Dict],
    ) -> List[Dict]:

        unique = {}

        for source in sources:

            key = (
                source.get("url"),
                source.get("angle"),
            )

            if key not in unique:
                unique[key] = source

        return list(
            unique.values()
        )