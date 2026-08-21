from query_engine.response_planner import ResponsePlanner
from query_engine.evidence_builder import EvidencePackage
from query_engine.schemas import QueryAnalysis


planner = ResponsePlanner()


evidence = EvidencePackage(
    question="What is hypertension?",
    combined_evidence="test evidence",
    evidence_by_angle={
        "definition": (
            "[who.int]\n"
            "Hypertension is high blood pressure."
        ),
        "symptoms": "No evidence retrieved.",
        "causes": (
            "[who.int]\n"
            "Several causes exist."
        ),
        "risk factors": (
            "[mayoclinic.org]\n"
            "Family history is a risk factor."
        ),
        "diagnosis": "No evidence retrieved.",
        "complications": (
            "[who.int]\n"
            "It can cause complications."
        ),
        "prevention": "No evidence retrieved.",
        "management and treatment": "No evidence retrieved.",
        "types": (
            "[mayoclinic.org]\n"
            "There are different types."
        ),
        "monitoring": (
            "[heart.org]\n"
            "Monitoring is important."
        ),
        "lifestyle": "No evidence retrieved.",
        "when to seek medical care": (
            "No evidence retrieved."
        ),
    },
    sources=[],
)


# --------------------------------------------------
# Definition
# --------------------------------------------------

definition_analysis = QueryAnalysis(
    original_question="What is hypertension?",
    topic="hypertension",
    intent="definition",
)

definition_plan = planner.plan(
    definition_analysis,
    evidence,
)

assert "definition" in (
    definition_plan.primary_angles
)

assert (
    definition_plan.generate_flashcards
    is True
)

assert (
    "definition"
    in definition_plan.flashcard_angles
)

assert (
    definition_plan.recommend_visual
    is True
)

assert (
    definition_plan.visual_angle
    == "definition"
)

assert (
    definition_plan.include_sources
    is True
)

assert (
    definition_plan.include_safety_note
    is False
)


# --------------------------------------------------
# Risk factors
# --------------------------------------------------

risk_analysis = QueryAnalysis(
    original_question=(
        "What increases the risk of hypertension?"
    ),
    topic="hypertension",
    intent="risk_factors",
)

risk_plan = planner.plan(
    risk_analysis,
    evidence,
)

assert (
    "risk factors"
    in risk_plan.primary_angles
)

assert (
    "risk factors"
    in risk_plan.flashcard_angles
)


# --------------------------------------------------
# Symptoms
# --------------------------------------------------

symptom_analysis = QueryAnalysis(
    original_question=(
        "What are the symptoms of hypertension?"
    ),
    topic="hypertension",
    intent="symptoms",
)

symptom_plan = planner.plan(
    symptom_analysis,
    evidence,
)

assert (
    symptom_plan.include_safety_note
    is True
)


# Symptoms have no evidence in this fixture,
# so visual support should not be falsely recommended.
assert (
    symptom_plan.recommend_visual
    is False
)


# --------------------------------------------------
# Treatment with missing treatment evidence
# --------------------------------------------------

treatment_analysis = QueryAnalysis(
    original_question=(
        "How is hypertension treated?"
    ),
    topic="hypertension",
    intent="treatment",
)

treatment_plan = planner.plan(
    treatment_analysis,
    evidence,
)

assert (
    treatment_plan.include_safety_note
    is True
)

assert (
    treatment_plan.primary_angles
)


print("=" * 70)
print("CARDIOGUIDE RESPONSE PLANNER TEST")
print("=" * 70)

print("\nDEFINITION PLAN:")
print("PRIMARY:", definition_plan.primary_angles)
print(
    "SUPPORTING:",
    definition_plan.supporting_angles,
)
print(
    "FLASHCARDS:",
    definition_plan.generate_flashcards,
)
print(
    "FLASHCARD ANGLES:",
    definition_plan.flashcard_angles,
)
print(
    "VISUAL:",
    definition_plan.recommend_visual,
)
print(
    "VISUAL ANGLE:",
    definition_plan.visual_angle,
)
print(
    "SAFETY:",
    definition_plan.include_safety_note,
)

print("\nRISK FACTOR PLAN:")
print("PRIMARY:", risk_plan.primary_angles)
print(
    "FLASHCARD ANGLES:",
    risk_plan.flashcard_angles,
)

print("\nSYMPTOM PLAN:")
print("PRIMARY:", symptom_plan.primary_angles)
print(
    "SAFETY:",
    symptom_plan.include_safety_note,
)
print(
    "VISUAL:",
    symptom_plan.recommend_visual,
)

print("\nTREATMENT PLAN:")
print("PRIMARY:", treatment_plan.primary_angles)
print(
    "SAFETY:",
    treatment_plan.include_safety_note,
)

print("\n" + "=" * 70)
print("STATUS: PASS")