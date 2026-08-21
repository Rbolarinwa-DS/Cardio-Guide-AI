from query_engine.schemas import QueryAnalysis


def apply_fallback(analysis: QueryAnalysis) -> QueryAnalysis:
    """
    Handles questions that were not found as exact matches
    in cardioguide_queries.csv.
    """

    # Already understood by the dataset
    if analysis.intent is not None:
        return analysis

    # No exact dataset match.
    # Keep the known information empty rather than inventing
    # an intent that the analyzer has not established.
    return QueryAnalysis(
        original_question=analysis.original_question,
        topic=analysis.topic,
        subtopic=analysis.subtopic,
        intent="general_information",
        explicit_depth=analysis.explicit_depth or "unknown",
        knowledge_level=analysis.knowledge_level or "unknown",
        user_goal=analysis.user_goal or "understand_concept",
        response_strategy="adaptive_explanation",
        visual_support=analysis.visual_support or "recommended",
    )