import os
import time
from dataclasses import dataclass
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv


load_dotenv()


@dataclass
class SearchResult:
    """
    A single search result tied to the research angle
    and query that produced it.
    """

    angle: str
    query: str
    result: dict


class WebSearcher:
    """
    Searches approved medical sources using the Serper API.

    Responsibilities:
        1. Execute research queries independently.
        2. Restrict results to approved medical domains.
        3. Preserve research angle and query provenance.
        4. Retry transient Serper/network failures.
        5. Handle individual search failures safely.
        6. Deduplicate results.
        7. Return multiple approved sources.

    The rest of CardioGuide does not need to know which
    search provider is being used.
    """

    SERPER_API_URL = (
        "https://google.serper.dev/search"
    )

    APPROVED_DOMAINS = {
        "who.int",
        "www.who.int",
        "mayoclinic.org",
        "www.mayoclinic.org",
        "heart.org",
        "www.heart.org",
    }

    APPROVED_BASE_DOMAINS = (
        "who.int",
        "mayoclinic.org",
        "heart.org",
    )

    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 15
    RETRY_DELAY = 1

    def __init__(self):
        # --------------------------------------------------
        # Load Serper API key
        # --------------------------------------------------

        api_key = os.getenv(
            "SERPER_API_KEY"
        )

        if not api_key:
            raise ValueError(
                "SERPER_API_KEY is missing "
                "from the .env file."
            )

        self.api_key = api_key

        # --------------------------------------------------
        # Reusable HTTP session
        # --------------------------------------------------

        self.session = requests.Session()

        self.session.headers.update(
            {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": (
                    "CardioGuide-AI/1.0 "
                    "(medical-research-engine)"
                ),
                "Connection": "keep-alive",
            }
        )

    # ==========================================================
    # DOMAIN VALIDATION
    # ==========================================================

    def _is_approved_domain(
        self,
        url: str,
    ) -> bool:
        """
        Return True only when the URL belongs to an
        approved medical domain.
        """

        if not url:
            return False

        try:
            hostname = urlparse(
                url
            ).hostname

        except Exception:
            return False

        if not hostname:
            return False

        hostname = (
            hostname
            .lower()
            .strip()
        )

        # Exact domain match
        if hostname in self.APPROVED_DOMAINS:
            return True

        # Allow legitimate subdomains
        return any(
            hostname.endswith(
                "." + domain
            )
            for domain in self.APPROVED_BASE_DOMAINS
        )

    # ==========================================================
    # QUERY EXTRACTION
    # ==========================================================

    def _extract_query(
        self,
        query_item,
    ) -> str:
        """
        Extract the search query from a ResearchQuery
        object or plain string.
        """

        if isinstance(
            query_item,
            str,
        ):
            return query_item.strip()

        if hasattr(
            query_item,
            "query",
        ):
            return str(
                query_item.query
            ).strip()

        return str(
            query_item
        ).strip()

    # ==========================================================
    # ANGLE EXTRACTION
    # ==========================================================

    def _extract_angle(
        self,
        query_item,
    ) -> str:
        """
        Extract the research angle from a ResearchQuery.
        """

        if hasattr(
            query_item,
            "angle",
        ):
            return str(
                query_item.angle
            ).strip()

        return ""

    # ==========================================================
    # SINGLE QUERY SEARCH
    # ==========================================================

    def _search_query(
        self,
        query: str,
        angle: str,
        max_sources: int,
    ) -> list[SearchResult]:
        """
        Execute one Serper search.

        Transient network failures are retried before the
        query is considered failed.

        One failed query does not destroy the entire
        CardioGuide research process.
        """

        if not query:
            return []

        payload = {
            "q": query,
            "num": max_sources,
        }

        response = None

        # --------------------------------------------------
        # Retry network failures
        # --------------------------------------------------

        for attempt in range(
            1,
            self.MAX_RETRIES + 1,
        ):

            try:
                response = self.session.post(
                    self.SERPER_API_URL,
                    json=payload,
                    timeout=self.REQUEST_TIMEOUT,
                )

                break

            except (
                requests.ConnectionError,
                requests.Timeout,
                requests.RequestException,
            ) as exc:

                print(
                    f"[WebSearcher] Request attempt "
                    f"{attempt}/{self.MAX_RETRIES} failed "
                    f"for angle='{angle}': {exc}"
                )

                if attempt < self.MAX_RETRIES:
                    time.sleep(
                        self.RETRY_DELAY * attempt
                    )

        # --------------------------------------------------
        # All attempts failed
        # --------------------------------------------------

        if response is None:

            print(
                f"[WebSearcher] Giving up on "
                f"angle='{angle}' after "
                f"{self.MAX_RETRIES} attempts."
            )

            return []

        # --------------------------------------------------
        # HTTP validation
        # --------------------------------------------------

        if response.status_code != 200:

            print(
                f"[WebSearcher] Serper returned "
                f"HTTP {response.status_code} "
                f"for angle='{angle}'."
            )

            try:
                print(
                    f"[WebSearcher] Response: "
                    f"{response.text[:500]}"
                )

            except Exception:
                pass

            return []

        # --------------------------------------------------
        # JSON parsing
        # --------------------------------------------------

        try:
            data = response.json()

        except ValueError:

            print(
                "[WebSearcher] Serper returned "
                "an invalid JSON response."
            )

            return []

        if not isinstance(
            data,
            dict,
        ):
            return []

        # --------------------------------------------------
        # Serper organic results
        # --------------------------------------------------

        organic_results = data.get(
            "organic",
            [],
        )

        if not isinstance(
            organic_results,
            list,
        ):
            return []

        approved_results = []

        for result in organic_results:

            if not isinstance(
                result,
                dict,
            ):
                continue

            url = str(
                result.get(
                    "link",
                    "",
                )
            ).strip()

            if not url:
                continue

            # --------------------------------------------------
            # Approved medical domain check
            # --------------------------------------------------

            if not self._is_approved_domain(
                url
            ):
                continue

            # --------------------------------------------------
            # Normalize Serper result
            # --------------------------------------------------

            normalized_result = {
                "title": str(
                    result.get(
                        "title",
                        "Untitled source",
                    )
                ).strip(),

                "url": url,

                "content": str(
                    result.get(
                        "snippet",
                        "",
                    )
                ).strip(),

                "snippet": str(
                    result.get(
                        "snippet",
                        "",
                    )
                ).strip(),
            }

            # --------------------------------------------------
            # Require useful evidence text
            # --------------------------------------------------

            if not normalized_result["content"]:
                continue

            approved_results.append(
                SearchResult(
                    angle=angle,
                    query=query,
                    result=normalized_result,
                )
            )

            if len(
                approved_results
            ) >= max_sources:
                break

        return approved_results

    # ==========================================================
    # SEARCH
    # ==========================================================

    def search(
        self,
        queries,
        max_sources: int = 3,
    ) -> list[SearchResult]:
        """
        Execute all research queries independently.

        max_sources is applied PER QUERY.

        Example:

            12 research queries
            × up to 3 sources
            = up to 36 raw results.

        Results are deduplicated before returning.
        """

        if not queries:
            return []

        collected_results = []

        # --------------------------------------------------
        # Execute every research query independently
        # --------------------------------------------------

        for query_item in queries:

            query = self._extract_query(
                query_item
            )

            angle = self._extract_angle(
                query_item
            )

            if not query:
                continue

            results = self._search_query(
                query=query,
                angle=angle,
                max_sources=max_sources,
            )

            collected_results.extend(
                results
            )

        # ==================================================
        # DEDUPLICATE
        # ==================================================

        unique_results = {}

        for search_result in collected_results:

            result = search_result.result

            url = str(
                result.get(
                    "url",
                    "",
                )
            ).strip()

            if not url:
                continue

            # Same URL can legitimately support different
            # research angles.
            key = (
                url,
                search_result.angle,
            )

            if key not in unique_results:
                unique_results[
                    key
                ] = search_result

        return list(
            unique_results.values()
        )