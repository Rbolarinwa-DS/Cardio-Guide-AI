from query_engine.evidence_builder import (
    EvidenceBuilder,
)
from query_engine.source_processor import ProcessedSource


builder = EvidenceBuilder()


sources = [
    ProcessedSource(
        title="WHO Hypertension",
        url=(
            "https://www.who.int/health-topics/"
            "hypertension"
        ),
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
        url=(
            "https://www.mayoclinic.org/"
            "diseases-conditions/high-blood-pressure"
        ),
        domain="mayoclinic.org",
        angle="risk factors",
        query=(
            "What are the risk factors "
            "for hypertension?"
        ),
        content=(
            "Risk factors include family history "
            "and obesity."
        ),
    ),
    ProcessedSource(
        title="AHA Hypertension",
        url=(
            "https://www.heart.org/en/"
            "health-topics/high-blood-pressure"
        ),
        domain="heart.org",
        angle="monitoring",
        query=(
            "How should hypertension "
            "be monitored?"
        ),
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

for angle, content in (
    evidence.evidence_by_angle.items()
):

    print(f"\n--- {angle.upper()} ---")
    print(content)


print("\nCLAIMS BY ANGLE:")

for angle, claims in (
    evidence.claims_by_angle.items()
):

    if not claims:
        continue

    print(f"\n--- {angle.upper()} ---")

    for index, claim in enumerate(
        claims,
        start=1,
    ):
        print(f"{index}. {claim['text']}")
        print(f"   SOURCE: {claim['title']}")
        print(f"   DOMAIN: {claim['domain']}")
        print(f"   URL: {claim['url']}")
        print(f"   QUERY: {claim['query']}")


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


# ============================================================
# ASSERTIONS
# ============================================================

assert (
    evidence.question
    == "What is hypertension?"
)

assert evidence.combined_evidence.strip()


# ============================================================
# ANGLE ISOLATION
# ============================================================

assert (
    "Hypertension is high blood pressure."
    in evidence.evidence_by_angle[
        "definition"
    ]
)

assert (
    "family history"
    in evidence.evidence_by_angle[
        "risk factors"
    ]
)

assert (
    "blood pressure monitoring"
    in evidence.evidence_by_angle[
        "monitoring"
    ]
)


# Evidence must NOT leak into unrelated angles.

assert (
    "Hypertension is high blood pressure."
    not in evidence.evidence_by_angle[
        "symptoms"
    ]
)

assert (
    "family history"
    not in evidence.evidence_by_angle[
        "diagnosis"
    ]
)


# ============================================================
# ALL ANGLES MUST EXIST
# ============================================================

assert (
    set(evidence.evidence_by_angle.keys())
    == set(EvidenceBuilder.ANGLES)
)

assert (
    set(evidence.claims_by_angle.keys())
    == set(EvidenceBuilder.ANGLES)
)


# ============================================================
# CLAIM STRUCTURE
# ============================================================

definition_claims = (
    evidence.claims_by_angle[
        "definition"
    ]
)

risk_claims = (
    evidence.claims_by_angle[
        "risk factors"
    ]
)

monitoring_claims = (
    evidence.claims_by_angle[
        "monitoring"
    ]
)


assert len(definition_claims) == 1
assert len(risk_claims) == 1
assert len(monitoring_claims) == 1


for claim in (
    definition_claims
    + risk_claims
    + monitoring_claims
):

    assert claim["text"]
    assert claim["title"]
    assert claim["url"]
    assert claim["domain"]
    assert claim["angle"]
    assert claim["query"]


# ============================================================
# SOURCE METADATA
# ============================================================

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


for source in evidence.sources:

    assert source["title"]
    assert source["url"]
    assert source["domain"]
    assert source["angle"]
    assert source["query"]


print("\n" + "=" * 70)
print("STATUS: PASS")
print("=" * 70)