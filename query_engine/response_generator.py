from typing import List

from query_engine.evidence_builder import EvidencePackage
from query_engine.response_planner import ResponsePlan


class ResponseGenerator:

    def generate(
        self,
        evidence: EvidencePackage,
        plan: ResponsePlan,
    ) -> dict:

        answer = self._build_answer(
            evidence,
            plan,
        )

        flashcards = self._build_flashcards(
            evidence,
            plan,
        )

        visual_support = self._build_visual_support(
            evidence,
            plan,
        )

        sources = self._build_sources(
            evidence,
        )

        safety_note = None

        if plan.include_safety_note:
            safety_note = (
                "This information is for education and "
                "does not replace assessment or advice "
                "from a qualified healthcare professional."
            )

        return {
            "answer": answer,
            "flashcards": flashcards,
            "visual_support": visual_support,
            "sources": sources,
            "safety_note": safety_note,
        }

    def _build_answer(
        self,
        evidence: EvidencePackage,
        plan: ResponsePlan,
    ) -> str:

        sections: List[str] = []

        for angle in plan.primary_angles:

            content = evidence.evidence_by_angle.get(
                angle,
                "",
            )

            if self._has_evidence(content):
                sections.append(
                    self._clean_evidence(content)
                )

        for angle in plan.supporting_angles:

            content = evidence.evidence_by_angle.get(
                angle,
                "",
            )

            if self._has_evidence(content):
                sections.append(
                    self._clean_evidence(content)
                )

        if not sections:
            return (
                "I could not retrieve enough reliable "
                "evidence from the approved medical sources "
                "to answer this question confidently."
            )

        return "\n\n".join(sections)

    def _build_flashcards(
        self,
        evidence: EvidencePackage,
        plan: ResponsePlan,
    ) -> List[dict]:

        if not plan.generate_flashcards:
            return []

        flashcards = []

        for angle in plan.flashcard_angles:

            content = evidence.evidence_by_angle.get(
                angle,
                "",
            )

            if not self._has_evidence(content):
                continue

            clean_content = self._clean_evidence(
                content
            )

            flashcards.append(
                {
                    "angle": angle,
                    "question": self._flashcard_question(
                        angle,
                        evidence.question,
                    ),
                    "answer": clean_content,
                }
            )

        return flashcards

    def _flashcard_question(
        self,
        angle: str,
        original_question: str,
    ) -> str:

        questions = {
            "definition": (
                "What is this condition?"
            ),
            "symptoms": (
                "What symptoms are associated "
                "with this condition?"
            ),
            "causes": (
                "What can cause this condition?"
            ),
            "risk factors": (
                "What are the major risk factors?"
            ),
            "diagnosis": (
                "How is this condition diagnosed?"
            ),
            "complications": (
                "What complications can it cause?"
            ),
            "prevention": (
                "How can it be prevented?"
            ),
            "management and treatment": (
                "How is it managed or treated?"
            ),
            "types": (
                "What are the main types?"
            ),
            "monitoring": (
                "How is it monitored?"
            ),
            "lifestyle": (
                "What lifestyle factors are relevant?"
            ),
            "when to seek medical care": (
                "When should medical care be sought?"
            ),
        }

        return questions.get(
            angle,
            original_question,
        )

    def _build_visual_support(
        self,
        evidence: EvidencePackage,
        plan: ResponsePlan,
    ) -> dict:

        if not plan.recommend_visual:
            return {
                "recommended": False,
                "angle": None,
                "reason": None,
            }

        angle = plan.visual_angle

        return {
            "recommended": True,
            "angle": angle,
            "reason": (
                f"A visual explanation may help the user "
                f"understand the {angle} aspect of the topic."
            ),
        }

    def _build_sources(
        self,
        evidence: EvidencePackage,
    ) -> List[dict]:

        return [
            {
                "title": source["title"],
                "url": source["url"],
                "domain": source["domain"],
                "angle": source.get("angle"),
            }
            for source in evidence.sources
        ]

    def _clean_evidence(
        self,
        content: str,
    ) -> str:

        lines = []

        for line in content.splitlines():

            line = line.strip()

            if not line:
                continue

            # Remove internal source labels from
            # the actual answer.
            if (
                line.startswith("[")
                and line.endswith("]")
            ):
                continue

            lines.append(line)

        return " ".join(lines)

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