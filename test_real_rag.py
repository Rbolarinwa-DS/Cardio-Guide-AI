from query_engine.schemas import QueryAnalysis
from query_engine.research_query_builder import ResearchQueryBuilder
from query_engine.web_searcher import WebSearcher
from query_engine.source_processor import SourceProcessor
from query_engine.evidence_builder import EvidenceBuilder
from query_engine.response_planner import ResponsePlanner
from query_engine.response_generator import ResponseGenerator


def main():
    question = (
        "What are the common symptoms of heart failure "
        "and when should someone seek urgent medical attention?"
    )

    print("\n=== 1. QUERY ANALYSIS ===")

    analysis = QueryAnalysis(
        original_question=question,
        topic="heart failure",
        intent="symptoms",
        explicit_depth="moderate",
        knowledge_level="general",
        user_goal="understand symptoms and urgency",
        response_strategy="educational",
        visual_support=None,
    )

    print(analysis)

    print("\n=== 2. RESEARCH PLAN ===")

    query_builder = ResearchQueryBuilder()
    research_plan = query_builder.build(analysis)

    print(f"Queries: {len(research_plan.queries)}")

    for q in research_plan.queries:
        print(f"- [{q.angle}] {q.query}")

    print("\n=== 3. WEB SEARCH ===")

    searcher = WebSearcher()

    raw_results = searcher.search(
        research_plan.queries,
        max_sources=3,
    )

    print(f"Raw results: {len(raw_results)}")

    for result in raw_results:
        print(
            f"- [{result.angle}] "
            f"{result.result.get('title', 'NO TITLE')} "
            f"{result.result.get('link', '')}"
        )

    print("\n=== 4. SOURCE PROCESSING ===")

    processor = SourceProcessor()
    processed_sources = processor.process(raw_results)

    print(f"Processed sources: {len(processed_sources)}")

    for source in processed_sources:
        print(
            f"- [{source.angle}] "
            f"{source.domain} | "
            f"{source.title}"
        )

    print("\n=== 5. EVIDENCE BUILDING ===")

    evidence_builder = EvidenceBuilder()
    evidence = evidence_builder.build(processed_sources)

    print(f"Evidence available: {evidence.has_evidence}")
    print(f"Angles: {evidence.available_angles}")
    print(f"Sources: {len(evidence.sources)}")

    for angle, claims in evidence.claims_by_angle.items():
        print(f"\nANGLE: {angle}")
        print(f"Claims: {len(claims)}")

        for claim in claims[:3]:
            print(f"  - {claim['text']}")
            print(f"    SOURCE: {claim['source_domain']}")

    print("\n=== 6. RESPONSE PLAN ===")

    planner = ResponsePlanner()
    response_plan = planner.plan(
        analysis,
        evidence,
    )

    print(response_plan)

    print("\n=== 7. RESPONSE GENERATION ===")

    generator = ResponseGenerator()

    result = generator.generate(
        evidence,
        response_plan,
    )

    print("\nANSWER:")
    print(result.get("answer", result))

    print("\nSOURCES:")

    for source in result.get("sources", []):
        print(
            f"- {source.get('title', '')} "
            f"| {source.get('url', '')}"
        )


if __name__ == "__main__":
    main()