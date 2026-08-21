from query_engine.schemas import QueryAnalysis
from query_engine.fallback import apply_fallback


class QueryRouter:

    def route(self, analysis: QueryAnalysis) -> dict:
        """
        Determines how CardioGuide should handle the analyzed query.

        The CSV is used for understanding the user's requested
        response style, not as the medical knowledge source.
        """

        # Known query pattern
        if analysis.intent is not None:
            return {
                "route": "known_query",
                "analysis": analysis,
                "research_required": True,
                "source_count": 3,
            }

        # Unknown query
        fallback_analysis = apply_fallback(analysis)

        return {
            "route": "unknown_query",
            "analysis": fallback_analysis,
            "research_required": True,
            "source_count": 3,
        }