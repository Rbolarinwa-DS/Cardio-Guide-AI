from dataclasses import dataclass
from typing import List

from query_engine.web_searcher import SearchResult


@dataclass
class ProcessedSource:
    title: str
    url: str
    domain: str
    content: str
    angle: str
    query: str


class SourceProcessor:

    ALLOWED_DOMAINS = {
        "who.int",
        "mayoclinic.org",
        "heart.org",
    }

    def process(
        self,
        results: List[SearchResult],
    ) -> List[ProcessedSource]:

        processed = []

        for item in results:

            result = item.result

            url = result.get("url", "").strip()

            if not url:
                continue

            domain = self._extract_domain(url)

            if domain not in self.ALLOWED_DOMAINS:
                continue

            title = result.get(
                "title",
                "Untitled source",
            ).strip()

            content = result.get(
                "content",
                "",
            ).strip()

            if not content:
                continue

            content = self._clean_content(content)

            if not content:
                continue

            processed.append(
                ProcessedSource(
                    title=title,
                    url=url,
                    domain=domain,
                    content=content,
                    angle=item.angle,
                    query=item.query,
                )
            )

        return self._remove_duplicates(processed)

    def _extract_domain(self, url: str) -> str:

        url = url.lower()

        url = url.replace(
            "https://",
            "",
        )

        url = url.replace(
            "http://",
            "",
        )

        domain = url.split("/")[0]

        if domain.startswith("www."):
            domain = domain[4:]

        return domain

    def _clean_content(
        self,
        content: str,
    ) -> str:

        junk_phrases = [
            "privacy policy",
            "terms of use",
            "cookie policy",
            "subscribe",
            "read more",
            "sign up",
            "©",
            "credits",
        ]

        lines = []

        for line in content.splitlines():

            cleaned = line.strip()

            if not cleaned:
                continue

            lower = cleaned.lower()

            if any(
                phrase in lower
                for phrase in junk_phrases
            ):
                continue

            lines.append(cleaned)

        return "\n".join(lines)

    def _remove_duplicates(
        self,
        sources: List[ProcessedSource],
    ) -> List[ProcessedSource]:

        unique = {}

        for source in sources:

            key = (
                source.url,
                source.angle,
            )

            if key not in unique:
                unique[key] = source

        return list(unique.values())