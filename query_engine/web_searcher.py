import os
from dataclasses import dataclass
from urllib.parse import urlparse

from dotenv import load_dotenv
from tavily import TavilyClient


load_dotenv()


@dataclass
class SearchResult:
    angle: str
    query: str
    result: dict


class WebSearcher:

    APPROVED_DOMAINS = {
        "who.int",
        "www.who.int",
        "mayoclinic.org",
        "www.mayoclinic.org",
        "heart.org",
        "www.heart.org",
    }

    def __init__(self):

        api_key = os.getenv("TAVILY_API_KEY")

        if not api_key:
            raise ValueError(
                "TAVILY_API_KEY is missing "
                "from the .env file."
            )

        self.client = TavilyClient(
            api_key=api_key
        )

    # --------------------------------------------------
    # DOMAIN VALIDATION
    # --------------------------------------------------

    def _is_approved_domain(self, url: str) -> bool:

        if not url:
            return False

        try:
            hostname = urlparse(url).hostname
        except Exception:
            return False

        if not hostname:
            return False

        hostname = hostname.lower()

        if hostname in self.APPROVED_DOMAINS:
            return True

        approved_base_domains = (
            "who.int",
            "mayoclinic.org",
            "heart.org",
        )

        return any(
            hostname.endswith(
                "." + domain
            )
            for domain in approved_base_domains
        )

    # --------------------------------------------------
    # QUERY EXTRACTION
    # --------------------------------------------------

    def _extract_query(self, query_item) -> str:

        if isinstance(query_item, str):
            return query_item.strip()

        if hasattr(query_item, "query"):
            return str(
                query_item.query
            ).strip()

        return str(
            query_item
        ).strip()

    # --------------------------------------------------
    # ANGLE EXTRACTION
    # --------------------------------------------------

    def _extract_angle(self, query_item) -> str:

        if hasattr(query_item, "angle"):
            return str(
                query_item.angle
            ).strip()

        return ""

    # --------------------------------------------------
    # SEARCH
    # --------------------------------------------------

    def search(
        self,
        queries,
        max_sources: int = 3,
    ) -> list[SearchResult]:

        collected_results = []

        for query_item in queries:

            query = self._extract_query(
                query_item
            )

            angle = self._extract_angle(
                query_item
            )

            if not query:
                continue

            try:

                response = self.client.search(
                    query=query,
                    search_depth="advanced",
                    max_results=3,
                )

            except Exception:

                # One failed query should not
                # stop the entire research process.
                continue

            if isinstance(
                response,
                dict,
            ):

                results = response.get(
                    "results",
                    []
                )

            else:

                results = getattr(
                    response,
                    "results",
                    []
                )

            if not results:
                continue

            for result in results:

                if not isinstance(
                    result,
                    dict,
                ):
                    continue

                url = result.get(
                    "url",
                    ""
                )

                if not self._is_approved_domain(
                    url
                ):
                    continue

                collected_results.append(
                    SearchResult(
                        angle=angle,
                        query=query,
                        result=result,
                    )
                )

        # --------------------------------------------------
        # DEDUPLICATE BY URL
        # --------------------------------------------------

        unique_results = {}

        for search_result in collected_results:

            url = search_result.result.get(
                "url",
                ""
            )

            if not url:
                continue

            if url not in unique_results:

                unique_results[
                    url
                ] = search_result

        # --------------------------------------------------
        # RETURN ONLY THE MAXIMUM NUMBER REQUESTED
        # --------------------------------------------------

        return list(
            unique_results.values()
        )[:max_sources]