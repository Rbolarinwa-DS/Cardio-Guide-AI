"""
Evidence construction layer for CardioGuide AI.

Pipeline:

    QueryAnalysis
        ↓
    ResearchQueryBuilder
        ↓
    WebSearcher
        ↓
    SourceProcessor
        ↓
    EvidenceBuilder
        ↓
    EvidencePackage
        ↓
    ResponsePlanner
        ↓
    ResponseGenerator

This module is responsible for organizing retrieved source material into
structured evidence. It does not generate medical claims or make clinical
decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


@dataclass
class ResearchQuery:
    """A single research query tied to a research angle."""

    angle: str
    query: str


@dataclass
class ResearchPlan:
    """Research plan produced from QueryAnalysis."""

    queries: List[ResearchQuery] = field(default_factory=list)


@dataclass
class EvidenceClaim:
    """A source-derived claim candidate."""

    text: str
    angle: str
    source_url: str
    source_title: str
    source_domain: str


@dataclass
class EvidenceSource:
    """A processed source available to the response system."""

    title: str
    url: str
    domain: str
    content: str
    angle: str
    query: str


@dataclass
class EvidencePackage:
    """
    Canonical evidence object passed to the response planner and generator.

    evidence_by_angle:
        Consolidated source text grouped by research angle.

    claims_by_angle:
        Sentence-level source-attributed claim candidates grouped by angle.

    sources:
        Source metadata preserving traceability to the original webpages.
    """

    evidence_by_angle: Dict[str, str] = field(default_factory=dict)
    claims_by_angle: Dict[str, List[Dict]] = field(default_factory=dict)
    sources: List[Dict] = field(default_factory=list)

    @property
    def available_angles(self) -> List[str]:
        """Return angles for which usable evidence exists."""

        return [
            angle
            for angle, content in self.evidence_by_angle.items()
            if content and content.strip()
        ]

    @property
    def has_evidence(self) -> bool:
        """Return whether the package contains usable evidence."""

        return bool(self.available_angles)


class EvidenceBuilder:
    """
    Convert processed web sources into an EvidencePackage.

    EvidenceBuilder organizes and preserves source material. It does not
    determine whether a medical statement is independently true.
    """

    MAX_SENTENCES_PER_SOURCE = 12
    MAX_CLAIMS_PER_SOURCE = 8
    MAX_CONTENT_CHARS = 6000

    def build(
        self,
        sources: Optional[List] = None,
    ) -> EvidencePackage:
        """
        Build an EvidencePackage from processed sources.

        Supported input:
        - SourceProcessor.ProcessedSource objects
        - dictionaries containing equivalent fields
        """

        package = EvidencePackage()

        if not sources:
            return package

        seen_source_urls = set()

        for source in sources:
            data = self._source_to_dict(source)

            url = self._clean_value(data.get("url"))

            if not url:
                continue

            if url in seen_source_urls:
                continue

            seen_source_urls.add(url)

            title = self._clean_value(data.get("title"))
            domain = self._clean_value(data.get("domain"))
            content = self._clean_content(data.get("content"))
            angle = (
                self._clean_value(data.get("angle"))
                or "general"
            )
            query = self._clean_value(data.get("query"))

            if not content:
                continue

            source_record = {
                "title": title,
                "url": url,
                "domain": domain,
                "angle": angle,
                "query": query,
            }

            package.sources.append(source_record)

            # Evidence is stored as one consolidated text block per angle.
            existing_content = package.evidence_by_angle.get(angle, "")

            if existing_content:
                package.evidence_by_angle[angle] = (
                    existing_content
                    + "\n\n"
                    + content
                )
            else:
                package.evidence_by_angle[angle] = content

            claims = self._extract_claims(
                content=content,
                angle=angle,
                source_record=source_record,
            )

            package.claims_by_angle.setdefault(angle, []).extend(
                claims
            )

        self._deduplicate_package(package)

        return package

    def _source_to_dict(self, source) -> Dict:
        """Normalize supported source object types into a dictionary."""

        if isinstance(source, dict):
            return source

        return {
            "title": getattr(source, "title", ""),
            "url": getattr(source, "url", ""),
            "domain": getattr(source, "domain", ""),
            "content": getattr(source, "content", ""),
            "angle": getattr(source, "angle", ""),
            "query": getattr(source, "query", ""),
        }

    def _clean_value(self, value) -> str:
        """Normalize a metadata value into a clean string."""

        if value is None:
            return ""

        return re.sub(
            r"\s+",
            " ",
            str(value),
        ).strip()

    def _clean_content(self, content) -> str:
        """
        Clean retrieved source text without rewriting its meaning.
        """

        if not content:
            return ""

        text = str(content)

        text = text.replace("\x00", " ")
        text = re.sub(r"\r\n?", "\n", text)

        lines = []

        for line in text.split("\n"):
            line = self._clean_value(line)

            if not line:
                continue

            if self._is_artifact(line):
                continue

            lines.append(line)

        text = " ".join(lines)

        text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        return text[: self.MAX_CONTENT_CHARS]

    def _is_artifact(self, text: str) -> bool:
        """Identify obvious webpage/navigation artifacts."""

        lower = text.lower().strip()

        artifact_patterns = (
            "skip to content",
            "menu",
            "search",
            "sign in",
            "log in",
            "subscribe",
            "cookie",
            "privacy policy",
            "terms of use",
            "advertisement",
            "share this",
            "facebook",
            "twitter",
            "instagram",
            "youtube",
        )

        if lower in artifact_patterns:
            return True

        if len(lower) <= 2:
            return True

        return False

    def _extract_claims(
        self,
        content: str,
        angle: str,
        source_record: Dict,
    ) -> List[Dict]:
        """
        Extract sentence-level evidence candidates.

        These remain source-attributed evidence candidates. They are not
        independently verified medical facts at this stage.
        """

        sentences = self._split_sentences(content)

        claims = []

        for sentence in sentences[: self.MAX_SENTENCES_PER_SOURCE]:
            sentence = sentence.strip()

            if not self._is_useful_sentence(sentence):
                continue

            claims.append(
                {
                    "text": sentence,
                    "angle": angle,
                    "source_url": source_record["url"],
                    "source_title": source_record["title"],
                    "source_domain": source_record["domain"],
                }
            )

            if len(claims) >= self.MAX_CLAIMS_PER_SOURCE:
                break

        return claims

    def _split_sentences(self, text: str) -> List[str]:
        """
        Conservatively split source content into sentences.

        No semantic rewriting is performed.
        """

        if not text:
            return []

        parts = re.split(
            r"(?<=[.!?])\s+",
            text,
        )

        return [
            part.strip()
            for part in parts
            if part and part.strip()
        ]

    def _is_useful_sentence(self, sentence: str) -> bool:
        """Filter obviously unusable sentence fragments."""

        if len(sentence) < 25:
            return False

        if len(sentence) > 700:
            return False

        lower = sentence.lower()

        if lower.startswith(
            (
                "click ",
                "read more",
                "learn more",
            )
        ):
            return False

        if re.fullmatch(
            r"[\W\d_]+",
            sentence,
        ):
            return False

        return True

    def _deduplicate_package(
        self,
        package: EvidencePackage,
    ) -> None:
        """
        Remove duplicate evidence and claims while preserving order.
        """

        for angle, content in list(
            package.evidence_by_angle.items()
        ):
            if not content:
                continue

            sentences = self._split_sentences(content)

            seen = set()
            unique_sentences = []

            for sentence in sentences:
                key = re.sub(
                    r"\s+",
                    " ",
                    sentence.lower(),
                ).strip()

                if key in seen:
                    continue

                seen.add(key)
                unique_sentences.append(sentence)

            package.evidence_by_angle[angle] = " ".join(
                unique_sentences
            )

        for angle, claims in list(
            package.claims_by_angle.items()
        ):
            seen = set()
            unique = []

            for claim in claims:
                key = re.sub(
                    r"\s+",
                    " ",
                    claim.get("text", "").lower(),
                ).strip()

                if not key or key in seen:
                    continue

                seen.add(key)
                unique.append(claim)

            package.claims_by_angle[angle] = unique