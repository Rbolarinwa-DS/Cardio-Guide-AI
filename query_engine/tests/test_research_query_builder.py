# query_engine/tests/test_research_query_builder.py

from query_engine.research_query_builder import (
    ResearchQueryBuilder,
)

from query_engine.schemas import QueryAnalysis


builder = ResearchQueryBuilder()


analysis = QueryAnalysis(
    original_question="What is hypertension?",
    topic="hypertension",
    intent="definition",
    knowledge_level="beginner",
    user_goal="understand hypertension",
)


plan = builder.build(analysis)


print("=" * 70)
print("CARDIOGUIDE RESEARCH QUERY BUILDER TEST")
print("=" * 70)

print("\nORIGINAL QUESTION:")
print(analysis.original_question)

print(f"\nRESEARCH QUERIES: {len(plan.queries)}")

for index, research_query in enumerate(
    plan.queries,
    start=1,
):
    print(f"\n{index}.")
    print(f"   ANGLE: {research_query.angle}")
    print(f"   QUERY: {research_query.query}")


print("\n" + "=" * 70)


# --------------------------------------------------
# Assertions
# --------------------------------------------------

expected_angles = [
    "definition",
    "symptoms",
    "causes",
    "risk factors",
    "diagnosis",
    "complications",
    "prevention",
    "management and treatment",
    "types",
    "monitoring",
    "lifestyle",
    "when to seek medical care",
]


# Exactly 12 research angles.
assert len(plan.queries) == 12


# Correct angle order.
actual_angles = [
    research_query.angle
    for research_query in plan.queries
]

assert actual_angles == expected_angles


# Every query must contain valid information.
for research_query in plan.queries:

    assert research_query.angle
    assert research_query.query

    assert (
        "hypertension"
        in research_query.query.lower()
    )


# Convert to lookup dictionary.
queries_by_angle = {
    research_query.angle: research_query.query
    for research_query in plan.queries
}


# --------------------------------------------------
# Verify individual research queries
# --------------------------------------------------

assert queries_by_angle["definition"] == (
    "What is hypertension?"
)

assert queries_by_angle["symptoms"] == (
    "What are the symptoms of hypertension?"
)

assert queries_by_angle["causes"] == (
    "What causes hypertension?"
)

assert queries_by_angle["risk factors"] == (
    "What are the risk factors for hypertension?"
)

assert queries_by_angle["diagnosis"] == (
    "How is hypertension diagnosed?"
)

assert queries_by_angle["complications"] == (
    "What complications can hypertension cause?"
)

assert queries_by_angle["prevention"] == (
    "How can hypertension be prevented?"
)

assert queries_by_angle[
    "management and treatment"
] == (
    "How is hypertension managed and treated?"
)

assert queries_by_angle["types"] == (
    "What are the different types of hypertension?"
)

assert queries_by_angle["monitoring"] == (
    "How should hypertension be monitored?"
)

assert queries_by_angle["lifestyle"] == (
    "What lifestyle factors are related to hypertension?"
)

assert queries_by_angle[
    "when to seek medical care"
] == (
    "When should someone seek medical care "
    "for hypertension?"
)


print("STATUS: PASS")