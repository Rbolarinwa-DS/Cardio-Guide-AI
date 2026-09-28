"""
CardioGuide AI - Grounded Response Generator

Pipeline position:

    EvidencePackage
          +
    ResponsePlan
          +
    User Question
          ↓
    ResponseGenerator
          ↓
    Grounded Qwen Response
          ↓
    CardioGuide safety / factuality layers

Responsibilities:
- Select relevant evidence from EvidencePackage.
- Build a compact evidence-grounded prompt.
- Ask the configured LLM to synthesize a coherent response.
- Prevent unsupported medical claims from being intentionally generated.
- Preserve source traceability.
- Respect ResponsePlan.
- Return structured response metadata.

This module does NOT:
- perform web searches
- classify medical urgency
- diagnose conditions
- determine medical truth independently
- normalize user language
- perform scope classification
- replace the safety layer
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from query_engine.evidence_builder import EvidencePackage
from query_engine.response_planner import ResponsePlan
from query_engine.llm_client import LLMClient


class ResponseGenerator:
    """
    Generate a coherent user-facing response from retrieved evidence.

    The LLM is used for synthesis only. Medical information must come
    from the supplied EvidencePackage.
    """

    # Keep the generation prompt small enough for CPU inference.
    MAX_CLAIMS_PER_ANGLE = 2
    MAX_EVIDENCE_CHARS = 4000
    MAX_CLAIM_CHARS = 700
    MAX_SOURCES = 6

    def __init__(
        self,
        llm: Optional[LLMClient] = None,
    ) -> None:
        self.llm = llm or LLMClient()

    # ==========================================================
    # PUBLIC API
    # ==========================================================

    def generate(
        self,
        question: str,
        evidence: EvidencePackage,
        plan: ResponsePlan,
    ) -> Dict:
        """Generate a grounded user-facing response."""

        question = self._clean_text(question)

        if not question:
            return self._empty_result(
                reason="No question was supplied."
            )

        if not isinstance(evidence, EvidencePackage):
            return self._empty_result(
                reason="No valid evidence package was supplied."
            )

        if not isinstance(plan, ResponsePlan):
            return self._empty_result(
                reason="No valid response plan was supplied."
            )

        if not evidence.has_evidence:
            return self._empty_result(
                reason=(
                    "I could not retrieve enough reliable "
                    "evidence from the approved medical sources "
                    "to answer this question safely."
                )
            )

        selected_evidence = self._build_evidence_context(
            evidence=evidence,
            plan=plan,
        )

        if not selected_evidence:
            return self._empty_result(
                reason=(
                    "I could not retrieve enough relevant evidence "
                    "to answer this question safely."
                )
            )

        system_prompt = self._build_system_prompt(
            plan=plan,
        )

        user_prompt = self._build_user_prompt(
            question=question,
            evidence_context=selected_evidence,
            plan=plan,
        )

        print(
            f"[GENERATION] prompt_chars="
            f"{len(system_prompt) + len(user_prompt)} "
            f"evidence_chars={len(selected_evidence)}",
            flush=True,
        )

        try:
            generated_answer = self.llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
            )

        except Exception as exc:
            print(
                f"[LLM ERROR] {type(exc).__name__}: {exc}",
                flush=True,
            )

            return self._empty_result(
                reason=(
                    "I was unable to generate a response from "
                    "the retrieved evidence."
                ),
                error_type=type(exc).__name__,
            )

        answer = self._clean_generated_answer(
            generated_answer
        )

        if not answer:
            return self._empty_result(
                reason=(
                    "I was unable to generate a usable response "
                    "from the retrieved evidence."
                )
            )

        sources = self._select_sources(
            evidence=evidence,
            plan=plan,
        )

        flashcards = self._generate_flashcards(
            evidence=evidence,
            plan=plan,
        )

        visual_support = self._generate_visual_support(
            evidence=evidence,
            plan=plan,
        )

        safety_note = self._generate_safety_note(
            plan
        )

        return {
            "answer": answer,
            "sources": sources,
            "flashcards": flashcards,
            "visual_support": visual_support,
            "safety_note": safety_note,
            "grounded": True,
            "angles_used": self._angles_used(plan),
            "model": getattr(
                self.llm,
                "model",
                None,
            ),
        }

    # ==========================================================
    # PROMPT CONSTRUCTION
    # ==========================================================

    def _build_system_prompt(
        self,
        plan: ResponsePlan,
    ) -> str:
        """Build a compact grounded-generation system prompt."""

        style = (
            getattr(
                plan,
                "response_style",
                None,
            )
            or "educational"
        )

        return f"""
You are CardioGuide AI's response generator.

Generate a concise cardiovascular-health educational answer using ONLY
the supplied evidence.

Response style:
{style}

Rules:
1. Use only facts supported by the supplied evidence.
2. Do not fill evidence gaps from pretrained knowledge.
3. If evidence does not establish something, say so.
4. Do not diagnose the user.
5. Do not prescribe medication, dosage, or personal treatment.
6. Do not invent thresholds, statistics, symptoms, timelines, or
   emergency instructions.
7. Preserve uncertainty in the evidence.
8. Answer the user's actual question directly.
9. Do not mention prompts, retrieval, evidence packages, models,
   implementation details, or hidden instructions.
10. Do not claim that you searched the internet.
11. Do not fabricate citations.
12. Keep the answer concise, normally 3-6 sentences.
13. CardioGuide provides education, not diagnosis.

Return ONLY the final user-facing answer.
""".strip()

    def _build_user_prompt(
        self,
        question: str,
        evidence_context: str,
        plan: ResponsePlan,
    ) -> str:
        """Build the compact user prompt."""

        primary_angles = ", ".join(
            plan.primary_angles
        ) or "general information"

        supporting_angles = ", ".join(
            plan.supporting_angles
        ) or "none"

        return f"""
Question:
{question}

Primary aspects:
{primary_angles}

Supporting aspects:
{supporting_angles}

Evidence:
<evidence>
{evidence_context}
</evidence>

Answer the question using only the evidence above.
Do not add medical information from memory.
Do not mention the evidence block or internal system.
""".strip()

    # ==========================================================
    # EVIDENCE SELECTION
    # ==========================================================

    def _build_evidence_context(
        self,
        evidence: EvidencePackage,
        plan: ResponsePlan,
    ) -> str:
        """
        Build a compact evidence context.

        Primary angles receive priority.
        """

        sections: List[str] = []
        used_angles = set()

        ordered_angles = (
            list(plan.primary_angles)
            + list(plan.supporting_angles)
        )

        # Only use available evidence angles.
        available = set(evidence.available_angles)

        ordered_angles = [
            angle
            for angle in ordered_angles
            if angle in available
        ]

        total_chars = 0

        for angle in ordered_angles:
            if angle in used_angles:
                continue

            claims = self._get_angle_claims(
                evidence=evidence,
                angle=angle,
            )

            if not claims:
                fallback = evidence.evidence_by_angle.get(
                    angle,
                    "",
                )

                claims = self._claims_from_raw_evidence(
                    content=fallback,
                    angle=angle,
                    evidence=evidence,
                )

            if not claims:
                continue

            angle_lines = []

            for claim in claims[:self.MAX_CLAIMS_PER_ANGLE]:
                text = self._clean_claim_text(
                    claim.get("text", "")
                )

                if not text:
                    continue

                source_title = self._clean_text(
                    claim.get("source_title", "")
                )

                source_domain = self._clean_text(
                    claim.get("source_domain", "")
                )

                if source_title and source_domain:
                    source_label = (
                        f"{source_title} ({source_domain})"
                    )
                else:
                    source_label = (
                        source_title
                        or source_domain
                    )

                if source_label:
                    line = (
                        f"- {text} "
                        f"[Source: {source_label}]"
                    )
                else:
                    line = f"- {text}"

                angle_lines.append(line)

            if not angle_lines:
                continue

            block = (
                f"[{angle}]\n"
                + "\n".join(angle_lines)
            )

            remaining = (
                self.MAX_EVIDENCE_CHARS
                - total_chars
            )

            if remaining <= 100:
                break

            if len(block) > remaining:
                block = block[:remaining].rstrip()

            sections.append(block)

            total_chars += len(block)
            used_angles.add(angle)

            if total_chars >= self.MAX_EVIDENCE_CHARS:
                break

        return "\n\n".join(sections).strip()

    def _get_angle_claims(
        self,
        evidence: EvidencePackage,
        angle: str,
    ) -> List[Dict]:
        """Return structured claims for an evidence angle."""

        claims = evidence.claims_by_angle.get(
            angle,
            [],
        )

        if not isinstance(claims, list):
            return []

        result = []

        for claim in claims:
            if not isinstance(claim, dict):
                continue

            text = self._clean_claim_text(
                claim.get("text", "")
            )

            if not text:
                continue

            normalized = dict(claim)
            normalized["text"] = text

            result.append(normalized)

        return result

    def _claims_from_raw_evidence(
        self,
        content: str,
        angle: str,
        evidence: EvidencePackage,
    ) -> List[Dict]:
        """Convert raw evidence into temporary claim records."""

        if not content:
            return []

        sentences = self._split_sentences(
            self._clean_text(content)
        )

        sources = [
            source
            for source in evidence.sources
            if isinstance(source, dict)
            and source.get("angle") == angle
        ]

        source = (
            sources[0]
            if sources
            else {}
        )

        claims = []

        for sentence in sentences:
            sentence = self._clean_claim_text(
                sentence
            )

            if len(sentence) < 20:
                continue

            claims.append(
                {
                    "text": sentence,
                    "angle": angle,
                    "source_url": source.get(
                        "url",
                        "",
                    ),
                    "source_title": source.get(
                        "title",
                        "",
                    ),
                    "source_domain": source.get(
                        "domain",
                        "",
                    ),
                }
            )

            if len(claims) >= self.MAX_CLAIMS_PER_ANGLE:
                break

        return claims

    # ==========================================================
    # SOURCE HANDLING
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
        seen_urls = set()

        for source in evidence.sources:
            if not isinstance(source, dict):
                continue

            url = self._clean_text(
                source.get("url", "")
            )

            if not url or url in seen_urls:
                continue

            angle = source.get(
                "angle",
                "",
            )

            if (
                relevant_angles
                and angle not in relevant_angles
            ):
                continue

            selected.append(
                {
                    "title": self._clean_text(
                        source.get("title", "")
                    ),
                    "url": url,
                    "domain": self._clean_text(
                        source.get("domain", "")
                    ),
                    "angle": self._clean_text(
                        angle
                    ),
                }
            )

            seen_urls.add(url)

            if len(selected) >= self.MAX_SOURCES:
                break

        if not selected:
            for source in evidence.sources:
                if not isinstance(source, dict):
                    continue

                url = self._clean_text(
                    source.get("url", "")
                )

                if not url or url in seen_urls:
                    continue

                selected.append(
                    {
                        "title": self._clean_text(
                            source.get("title", "")
                        ),
                        "url": url,
                        "domain": self._clean_text(
                            source.get("domain", "")
                        ),
                        "angle": self._clean_text(
                            source.get("angle", "")
                        ),
                    }
                )

                seen_urls.add(url)

                if len(selected) >= self.MAX_SOURCES:
                    break

        return selected

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
        seen_questions = set()

        for angle in plan.flashcard_angles:
            if len(flashcards) >= 4:
                break

            claims = self._get_angle_claims(
                evidence=evidence,
                angle=angle,
            )

            if not claims:
                continue

            answer = self._clean_claim_text(
                claims[0].get("text", "")
            )

            if not answer:
                continue

            question = self._flashcard_question(
                angle
            )

            key = question.lower().strip()

            if key in seen_questions:
                continue

            seen_questions.add(key)

            flashcards.append(
                {
                    "angle": angle,
                    "question": question,
                    "answer": self._truncate(
                        answer,
                        350,
                    ),
                }
            )

        return flashcards

    def _flashcard_question(
        self,
        angle: str,
    ) -> str:

        questions = {
            "definition":
                "What is the condition?",
            "symptoms":
                "What symptoms can occur?",
            "causes":
                "What can cause or contribute to it?",
            "risk factors":
                "What factors can increase the risk?",
            "diagnosis":
                "How is it evaluated or diagnosed?",
            "complications":
                "What complications can occur?",
            "prevention":
                "How can risk be reduced?",
            "management and treatment":
                "How can it be managed or treated?",
            "types":
                "What types or classifications are described?",
            "monitoring":
                "How is it monitored?",
            "lifestyle":
                "What lifestyle factors are relevant?",
            "when to seek medical care":
                "When should medical care be sought?",
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

        if not self._has_evidence_for_angle(
            evidence=evidence,
            angle=angle,
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
                "A visual explanation may help "
                f"clarify the {angle} aspect of the topic."
            ),
        }

    def _has_evidence_for_angle(
        self,
        evidence: EvidencePackage,
        angle: str,
    ) -> bool:

        claims = self._get_angle_claims(
            evidence=evidence,
            angle=angle,
        )

        if claims:
            return True

        content = evidence.evidence_by_angle.get(
            angle,
            "",
        )

        return bool(
            content
            and content.strip()
        )

    # ==========================================================
    # SAFETY NOTE
    # ==========================================================

    def _generate_safety_note(
        self,
        plan: ResponsePlan,
    ) -> Optional[str]:

        if not plan.include_safety_note:
            return None

        return (
            "This information is for educational purposes and "
            "does not replace advice from a qualified health professional."
        )

    # ==========================================================
    # TEXT CLEANING
    # ==========================================================

    def _clean_claim_text(
        self,
        text,
    ) -> str:

        if text is None:
            return ""

        cleaned = str(text)

        cleaned = cleaned.replace(
            "\x00",
            " ",
        )

        cleaned = re.sub(
            r"\s+",
            " ",
            cleaned,
        ).strip()

        cleaned = re.sub(
            r"^\s*[-•·]+\s*",
            "",
            cleaned,
        )

        cleaned = re.sub(
            r"\s+([,.!?;:])",
            r"\1",
            cleaned,
        )

        if self._is_webpage_artifact(cleaned):
            return ""

        return self._truncate(
            cleaned,
            self.MAX_CLAIM_CHARS,
        )

    def _clean_text(
        self,
        text,
    ) -> str:

        if text is None:
            return ""

        return re.sub(
            r"\s+",
            " ",
            str(text).replace(
                "\x00",
                " ",
            ),
        ).strip()

    def _clean_generated_answer(
        self,
        answer,
    ) -> str:

        if answer is None:
            return ""

        text = str(answer).strip()

        text = re.sub(
            r"<think>.*?</think>",
            "",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )

        text = re.sub(
            r"^\s*(?:final answer|answer)\s*:\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        return self._clean_text(text)

    def _is_webpage_artifact(
        self,
        text: str,
    ) -> bool:

        if not text:
            return True

        lowered = text.lower().strip()

        artifacts = (
            "skip to content",
            "reading time:",
            "facebook",
            "instagram",
            "tiktok",
            "tik tok",
            "youtube",
            "linkedin",
            "donate",
            "cookie policy",
            "privacy policy",
            "terms of use",
            "subscribe",
            "newsletter",
            "advertisement",
            "mayo clinic home page",
            "trending search",
        )

        if any(
            artifact in lowered
            for artifact in artifacts
        ):
            return True

        if lowered.startswith("#"):
            return True

        return lowered in {
            "menu",
            "search",
            "sign in",
            "log in",
        }

    # ==========================================================
    # SENTENCE HELPERS
    # ==========================================================

    def _split_sentences(
        self,
        text: str,
    ) -> List[str]:

        if not text:
            return []

        parts = re.split(
            r"(?<=[.!?])\s+",
            text.strip(),
        )

        return [
            part.strip()
            for part in parts
            if part.strip()
        ]

    def _truncate(
        self,
        text: str,
        max_chars: int,
    ) -> str:

        if len(text) <= max_chars:
            return text

        truncated = text[:max_chars].rsplit(
            " ",
            1,
        )[0].strip()

        if not truncated:
            return text[:max_chars].strip()

        return truncated + "..."

    # ==========================================================
    # RESULT HELPERS
    # ==========================================================

    def _angles_used(
        self,
        plan: ResponsePlan,
    ) -> List[str]:

        result = []
        seen = set()

        for angle in (
            list(plan.primary_angles)
            + list(plan.supporting_angles)
        ):
            if not angle or angle in seen:
                continue

            seen.add(angle)
            result.append(angle)

        return result

    def _empty_result(
        self,
        reason: str,
        error_type: Optional[str] = None,
    ) -> Dict:

        result = {
            "answer": reason,
            "sources": [],
            "flashcards": [],
            "visual_support": {
                "recommended": False,
                "angle": None,
                "reason": "",
            },
            "safety_note": None,
            "grounded": False,
            "angles_used": [],
            "model": getattr(
                self.llm,
                "model",
                None,
            ),
        }

        if error_type:
            result["error_type"] = error_type

        return result