from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class FactualityResult:
    """
    Result of evidence-aware factuality validation.
    """

    answer: str
    factual: bool
    grounded: bool

    supported_claims: List[str]
    unsupported_claims: List[str]
    contradictions: List[str]

    sources: List[str]

    confidence: Optional[float] = None


class FactualityLayer:
    """
    Evidence-aware factuality validation layer.

    Safety and factuality are intentionally separate.

    Safety asks:

        "Is this response allowed and safe?"

    Factuality asks:

        "Is there evidence available to support this answer?"

    IMPORTANT:

    This class does NOT claim that an answer is factual merely
    because evidence documents exist.

    Full claim-level entailment requires a finalized retrieval
    structure and verification mechanism.

    Until that exists, this layer remains conservative.
    """

    def validate(
        self,
        answer: str,
        evidence: Optional[List[dict]] = None,
    ) -> FactualityResult:

        # --------------------------------------------------------
        # Invalid answer
        # --------------------------------------------------------

        if not isinstance(answer, str):

            return FactualityResult(
                answer="",
                factual=False,
                grounded=False,
                supported_claims=[],
                unsupported_claims=[
                    "Generated answer is not a valid string."
                ],
                contradictions=[],
                sources=[],
                confidence=0.0,
            )

        answer = answer.strip()

        if not answer:

            return FactualityResult(
                answer="",
                factual=False,
                grounded=False,
                supported_claims=[],
                unsupported_claims=[
                    "Generated answer is empty."
                ],
                contradictions=[],
                sources=[],
                confidence=0.0,
            )

        # --------------------------------------------------------
        # Validate evidence container
        # --------------------------------------------------------

        if evidence is None:
            evidence = []

        if not isinstance(evidence, list):

            return FactualityResult(
                answer=answer,
                factual=False,
                grounded=False,
                supported_claims=[],
                unsupported_claims=[
                    "Evidence must be provided as a list."
                ],
                contradictions=[],
                sources=[],
                confidence=0.0,
            )

        valid_evidence = [
            item
            for item in evidence
            if isinstance(item, dict)
        ]

        # --------------------------------------------------------
        # No evidence
        # --------------------------------------------------------

        if not valid_evidence:

            return FactualityResult(
                answer=answer,
                factual=False,
                grounded=False,
                supported_claims=[],
                unsupported_claims=[
                    "No supporting evidence was available."
                ],
                contradictions=[],
                sources=[],
                confidence=0.0,
            )

        sources = self._extract_sources(
            valid_evidence
        )

        # --------------------------------------------------------
        # Evidence exists.
        #
        # Do NOT falsely label the answer factual.
        # Retrieval presence != claim-level entailment.
        # --------------------------------------------------------

        return FactualityResult(
            answer=answer,
            factual=False,
            grounded=False,
            supported_claims=[],
            unsupported_claims=[
                "Evidence was retrieved, but claim-level "
                "factuality verification has not yet been "
                "performed."
            ],
            contradictions=[],
            sources=sources,
            confidence=0.0,
        )

    # ============================================================
    # SOURCE EXTRACTION
    # ============================================================

    @staticmethod
    def _extract_sources(
        evidence: List[dict],
    ) -> List[str]:

        sources: List[str] = []

        for item in evidence:

            if not isinstance(item, dict):
                continue

            # URL
            url = item.get("url")

            if isinstance(url, str) and url.strip():
                sources.append(url.strip())
                continue

            # Source
            source = item.get("source")

            if isinstance(source, str) and source.strip():
                sources.append(source.strip())
                continue

            # Title
            title = item.get("title")

            if isinstance(title, str) and title.strip():
                sources.append(title.strip())
                continue

            # Optional metadata structure
            metadata = item.get("metadata")

            if isinstance(metadata, dict):

                metadata_url = metadata.get("url")

                if (
                    isinstance(metadata_url, str)
                    and metadata_url.strip()
                ):
                    sources.append(
                        metadata_url.strip()
                    )
                    continue

                metadata_source = metadata.get(
                    "source"
                )

                if (
                    isinstance(metadata_source, str)
                    and metadata_source.strip()
                ):
                    sources.append(
                        metadata_source.strip()
                    )

        # Preserve order while removing duplicates.
        return list(dict.fromkeys(sources))