from query_engine.response_generator import ResponseGenerator
from query_engine.response_planner import ResponsePlan
from query_engine.evidence_builder import EvidencePackage


generator = ResponseGenerator()


evidence = EvidencePackage(
    question="What is hypertension?",
    combined_evidence="test evidence",
    evidence_by_angle={
        "definition": (
            "[who.int]\n"
            "Hypertension is high blood pressure."
        ),
        "symptoms": "No evidence retrieved.",
        "causes": "No evidence retrieved.",
        "risk factors": (
            "[mayoclinic.org]\n"
            "Family history and obesity are risk factors."
        ),
        "diagnosis": "No evidence retrieved.",
        "complications": (
            "[who.int]\n"
            "Hypertension can cause cardiovascular complications."
        ),
        "prevention": "No evidence retrieved.",
        "management and treatment": "No evidence retrieved.",
        "types": "No evidence retrieved.",
        "monitoring": (
            "[heart.org]\n"
            "Regular blood pressure monitoring is important."
        ),
        "lifestyle": "No evidence retrieved.",
        "when to seek medical care": "No evidence retrieved.",
    },
    sources=[
        {
            "title": "WHO Hypertension",
            "url": "https://www.who.int/health-topics/hypertension",
            "domain": "who.int",
            "angle": "definition",
        },
        {
            "title": "Mayo Clinic Hypertension",
            "url": "https://www.mayoclinic.org/diseases-conditions/high-blood-pressure",
            "domain": "mayoclinic.org",
            "angle": "risk factors",
        },
        {
            "title": "AHA Hypertension",
            "url": "https://www.heart.org/en/health-topics/high-blood-pressure",
            "domain": "heart.org",
            "angle": "monitoring",
        },
    ],
)


plan = ResponsePlan(
    primary_angles=[
        "definition",
    ],
    supporting_angles=[
        "risk factors",
        "monitoring",
    ],
    response_style="clear educational explanation",
    include_sources=True,
    include_safety_note=False,
    generate_flashcards=True,
    flashcard_angles=[
        "definition",
        "risk factors",
    ],
    recommend_visual=True,
    visual_angle="definition",
)


result = generator.generate(
    evidence,
    plan,
)


print("=" * 70)
print("CARDIOGUIDE RESPONSE GENERATOR TEST")
print("=" * 70)

print("\nANSWER:")
print(result["answer"])

print("\nFLASHCARDS:")

for card in result["flashcards"]:
    print(f"\nANGLE: {card['angle']}")
    print(f"Q: {card['question']}")
    print(f"A: {card['answer']}")

print("\nVISUAL SUPPORT:")
print(result["visual_support"])

print("\nSAFETY NOTE:")
print(result["safety_note"])

print("\nSOURCES:")

for source in result["sources"]:
    print(
        f"- {source['title']} "
        f"({source['domain']})"
    )

print("\n" + "=" * 70)


# --------------------------------------------------
# Assertions
# --------------------------------------------------

assert result["answer"]

assert (
    "Hypertension is high blood pressure."
    in result["answer"]
)

# Source labels must not leak into the answer.
assert "[who.int]" not in result["answer"]

# Flashcards must be generated.
assert result["flashcards"]

assert len(result["flashcards"]) == 2

assert (
    result["flashcards"][0]["angle"]
    == "definition"
)

assert (
    result["flashcards"][1]["angle"]
    == "risk factors"
)

# Visual support must be enabled.
assert (
    result["visual_support"]["recommended"]
    is True
)

assert (
    result["visual_support"]["angle"]
    == "definition"
)

# Safety is disabled for this definition example.
assert result["safety_note"] is None

# Sources survive.
assert len(result["sources"]) == 3

assert {
    source["domain"]
    for source in result["sources"]
} == {
    "who.int",
    "mayoclinic.org",
    "heart.org",
}


print("STATUS: PASS")