from query_engine.evidence_builder import EvidenceBuilder
from query_engine.source_processor import ProcessedSource


builder = EvidenceBuilder()


sources = [
    ProcessedSource(
        title="WHO Hypertension",
        url="https://www.who.int/health-topics/hypertension",
        domain="who.int",
        angle="definition",
        query="What is hypertension?",
        content=(
            "Hypertension is high blood pressure. "
            "It increases the risk of cardiovascular disease."
        ),
    ),

    ProcessedSource(
        title="Mayo Clinic Hypertension",
        url="https://www.mayoclinic.org/diseases-conditions/high-blood-pressure",
        domain="mayoclinic.org",
        angle="risk factors",
        query="What are the risk factors for hypertension?",
        content=(
            "Risk factors include family history "
            "and obesity."
        ),
    ),

    ProcessedSource(
        title="AHA Hypertension",
        url="https://www.heart.org/en/health-topics/high-blood-pressure",
        domain="heart.org",
        angle="monitoring",
        query="How should hypertension be monitored?",
        content=(
            "Regular blood pressure monitoring "
            "is important."
        ),
    ),
]


evidence = builder.build(
    question="What is hypertension?",
    sources=sources,
)


print("=" * 70)
print("CARDIOGUIDE STRUCTURED EVIDENCE BUILDER TEST")
print("=" * 70)

print("\nQUESTION:")
print(evidence.question)

print("\nCOMBINED EVIDENCE:")
print(evidence.combined_evidence)

print("\nEVIDENCE BY ANGLE:")

for angle, content in evidence.evidence_by_angle.items():

    print(f"\n--- {angle.upper()} ---")
    print(content)

print("\nSOURCES:")

for index, source in enumerate(
    evidence.sources,
    start=1,
):

    print(f"\n{index}. {source['title']}")
    print(f"   DOMAIN: {source['domain']}")
    print(f"   ANGLE: {source['angle']}")
    print(f"   QUERY: {source['query']}")
    print(f"   URL: {source['url']}")

print("\n" + "=" * 70)


# --------------------------------------------------
# Assertions
# --------------------------------------------------

assert evidence.question == (
    "What is hypertension?"
)

assert evidence.combined_evidence.strip()


# Correct evidence must be attached to
# the angle that produced it.

assert (
    "Hypertension is high blood pressure."
    in evidence.evidence_by_angle["definition"]
)

assert (
    "family history"
    in evidence.evidence_by_angle["risk factors"]
)

assert (
    "blood pressure monitoring"
    in evidence.evidence_by_angle["monitoring"]
)


# Evidence must NOT leak into unrelated angles.

assert (
    "Hypertension is high blood pressure."
    not in evidence.evidence_by_angle["symptoms"]
)

assert (
    "family history"
    not in evidence.evidence_by_angle["diagnosis"]
)


# All 12 angles must exist.

assert set(
    evidence.evidence_by_angle.keys()
) == set(EvidenceBuilder.ANGLES)


# Three source records must survive.

assert len(evidence.sources) == 3


domains = {
    source["domain"]
    for source in evidence.sources
}

assert domains == {
    "who.int",
    "mayoclinic.org",
    "heart.org",
}


# Metadata must survive.

for source in evidence.sources:

    assert source["title"]
    assert source["url"]
    assert source["domain"]
    assert source["angle"]
    assert source["query"]


print("STATUS: PASS")