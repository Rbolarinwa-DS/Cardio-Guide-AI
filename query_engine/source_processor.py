from dataclasses import dataclass
from typing import List
from urllib.parse import urlparse
import re

from query_engine.web_searcher import SearchResult


@dataclass
class ProcessedSource:
    """
    Cleaned and validated source passed into the evidence-building stage.
    """

    title: str
    url: str
    domain: str
    content: str
    angle: str
    query: str


class SourceProcessor:
    """
    Validates, cleans, and deduplicates web-search results.

    Responsibilities:
        1. Validate source structure.
        2. Restrict sources to approved medical domains.
        3. Clean navigation and webpage boilerplate.
        4. Preserve medically relevant content.
        5. Preserve source provenance.
        6. Remove duplicate sources.
    """

    ALLOWED_DOMAINS = {
        "who.int",
        "mayoclinic.org",
        "heart.org",
    }

    # ============================================================
    # WEBPAGE BOILERPLATE
    # ============================================================

    JUNK_PHRASES = [
        "privacy policy",
        "terms of use",
        "terms and conditions",
        "cookie policy",
        "cookie settings",
        "subscribe",
        "sign up",
        "sign in",
        "log in",
        "login",
        "read more",
        "share this",
        "follow us",
        "contact us",
        "all rights reserved",
        "credits",
        "copyright",
        "advertisement",
        "advertising",
        "skip to content",
        "skip to main content",
        "menu",
        "search",
        "home",
        "navigation",
    ]

    # ============================================================
    # MAIN PROCESSING PIPELINE
    # ============================================================

    def process(
        self,
        results: List[SearchResult],
    ) -> List[ProcessedSource]:
        """
        Convert raw search results into validated ProcessedSource objects.
        """

        processed: List[ProcessedSource] = []

        for item in results:

            # ----------------------------------------------------
            # Validate search-result wrapper.
            # ----------------------------------------------------

            result = getattr(
                item,
                "result",
                None,
            )

            if not isinstance(result, dict):
                continue

            # ----------------------------------------------------
            # Extract URL.
            # ----------------------------------------------------

            url = str(
                result.get(
                    "url",
                    "",
                )
            ).strip()

            if not url:
                continue

            # ----------------------------------------------------
            # Validate domain.
            # ----------------------------------------------------

            domain = self._extract_domain(url)

            if domain not in self.ALLOWED_DOMAINS:
                continue

            # ----------------------------------------------------
            # Extract metadata.
            # ----------------------------------------------------

            title = str(
                result.get(
                    "title",
                    "Untitled source",
                )
            ).strip()

            content = str(
                result.get(
                    "content",
                    "",
                )
            ).strip()

            if not content:
                continue

            # ----------------------------------------------------
            # Clean webpage content.
            # ----------------------------------------------------

            content = self._clean_content(
                content
            )

            if not content:
                continue

            # ----------------------------------------------------
            # Preserve the angle and query assigned during
            # research-query construction.
            # ----------------------------------------------------

            angle = str(
                getattr(
                    item,
                    "angle",
                    "",
                )
            ).strip()

            query = str(
                getattr(
                    item,
                    "query",
                    "",
                )
            ).strip()

            if not angle:
                continue

            processed.append(
                ProcessedSource(
                    title=title,
                    url=url,
                    domain=domain,
                    content=content,
                    angle=angle,
                    query=query,
                )
            )

        return self._remove_duplicates(
            processed
        )

    # ============================================================
    # DOMAIN EXTRACTION
    # ============================================================

    def _extract_domain(
        self,
        url: str,
    ) -> str:
        """
        Extract a normalized hostname from a URL.
        """

        try:
            parsed = urlparse(url)

            domain = (
                parsed.netloc
                or parsed.path.split("/")[0]
            )

        except Exception:
            domain = url.split("/")[0]

        domain = (
            domain
            .lower()
            .strip()
        )

        if domain.startswith("www."):
            domain = domain[4:]

        # Remove a possible port.
        domain = domain.split(":")[0]

        return domain

    # ============================================================
    # CONTENT CLEANING
    # ============================================================

    def _clean_content(
        self,
        content: str,
    ) -> str:
        """
        Remove obvious webpage boilerplate while preserving
        meaningful medical text.
        """

        # --------------------------------------------------------
        # Normalize line endings and non-breaking spaces.
        # --------------------------------------------------------

        content = (
            content
            .replace("\r\n", "\n")
            .replace("\r", "\n")
            .replace("\xa0", " ")
        )

        cleaned_blocks: List[str] = []

        for line in content.splitlines():

            line = line.strip()

            if not line:
                continue

            lower_line = line.lower()

            # ----------------------------------------------------
            # Remove obvious navigation-only lines.
            # ----------------------------------------------------

            if self._is_junk_line(
                lower_line
            ):
                continue

            # ----------------------------------------------------
            # Remove boilerplate embedded inside useful text.
            # ----------------------------------------------------

            line = self._remove_inline_junk(
                line
            )

            line = line.strip()

            if not line:
                continue

            cleaned_blocks.append(
                line
            )

        # --------------------------------------------------------
        # Reconstruct text.
        # --------------------------------------------------------

        cleaned = "\n".join(
            cleaned_blocks
        )

        # --------------------------------------------------------
        # Normalize whitespace.
        # --------------------------------------------------------

        cleaned = re.sub(
            r"\s+",
            " ",
            cleaned,
        )

        return cleaned.strip()

    # ============================================================
    # JUNK LINE DETECTION
    # ============================================================

    def _is_junk_line(
        self,
        lower_line: str,
    ) -> bool:
        """
        Determine whether an entire line is webpage boilerplate.
        """

        normalized = (
            lower_line
            .strip()
        )

        # --------------------------------------------------------
        # Exact boilerplate matches.
        # --------------------------------------------------------

        if normalized in self.JUNK_PHRASES:
            return True

        # --------------------------------------------------------
        # WHO regional navigation often arrives as one giant line.
        #
        # Example:
        # Africa Americas South-East Asia Europe ...
        # --------------------------------------------------------

        who_navigation_markers = [
            "africa",
            "americas",
            "europe",
            "south-east asia",
            "eastern mediterranean",
            "western pacific",
        ]

        regional_matches = sum(
            marker in normalized
            for marker in who_navigation_markers
        )

        if regional_matches >= 3:
            return True

        # --------------------------------------------------------
        # Very short navigation labels.
        # --------------------------------------------------------

        if len(normalized) <= 30:

            for phrase in self.JUNK_PHRASES:

                if normalized == phrase:
                    return True

        return False

    # ============================================================
    # INLINE JUNK REMOVAL
    # ============================================================

    def _remove_inline_junk(
        self,
        line: str,
    ) -> str:
        """
        Remove boilerplate fragments without deleting the
        surrounding medical sentence.
        """

        cleaned = line

        # --------------------------------------------------------
        # Remove common legal/navigation fragments.
        # --------------------------------------------------------

        inline_patterns = [
            r"\bprivacy policy\b",
            r"\bterms of use\b",
            r"\bterms and conditions\b",
            r"\bcookie policy\b",
            r"\bcookie settings\b",
            r"\bsubscribe\b",
            r"\bsign up\b",
            r"\bsign in\b",
            r"\blog in\b",
            r"\blogin\b",
            r"\bread more\b",
            r"\bshare this\b",
            r"\bfollow us\b",
            r"\bcontact us\b",
            r"\badvertisement\b",
            r"\badvertising\b",
            r"\ball rights reserved\b",
        ]

        for pattern in inline_patterns:

            cleaned = re.sub(
                pattern,
                "",
                cleaned,
                flags=re.IGNORECASE,
            )

        # --------------------------------------------------------
        # Remove isolated copyright fragments.
        # --------------------------------------------------------

        cleaned = re.sub(
            r"©\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r"\bcredits?\b",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        # --------------------------------------------------------
        # Remove repeated whitespace.
        # --------------------------------------------------------

        cleaned = re.sub(
            r"\s+",
            " ",
            cleaned,
        )

        return cleaned.strip()

    # ============================================================
    # DUPLICATE REMOVAL
    # ============================================================

    def _remove_duplicates(
        self,
        sources: List[ProcessedSource],
    ) -> List[ProcessedSource]:
        """
        Remove duplicate source-angle combinations.

        The same URL can legitimately contribute evidence to
        different angles, so the angle is part of the identity key.
        """

        unique = {}

        for source in sources:

            key = (
                source.url,
                source.angle,
            )

            if key not in unique:
                unique[key] = source

        return list(
            unique.values()
        )