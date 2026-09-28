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
    claims_by_angle={
        "definition": [
            {
                "text": "Hypertension is high blood pressure.",
                "domain": "who.int",
                "title": "WHO Hypertension",
                "url": "https://www.who.int/health-topics/hypertension",
                "angle": "definition",
                "query": "What is hypertension?",
            }
        ],
        "symptoms": [],
        "causes": [],
        "risk factors": [
            {
                "text": "Family history is a risk factor.",
                "domain": "mayoclinic.org",
                "title": "Mayo Clinic Hypertension",
                "url": (
                    "https://www.mayoclinic.org/"
                    "diseases-conditions/high-blood-pressure"
                ),
                "angle": "risk factors",
                "query": (
                    "What increases the risk of hypertension?"
                ),
            }
        ],
        "diagnosis": [],
        "complications": [],
        "prevention": [],
        "management and treatment": [],
        "types": [],
        "monitoring": [],
        "lifestyle": [],
        "when to seek medical care": [],
    },
    sources=[],
)


# ============================================================
# DEFINITION
# ============================================================

definition_analysis = QueryAnalysis(
    original_question="What is hypertension?",
    topic="hypertension",
    intent="definition",
)

definition_plan = planner.plan(
    definition_analysis,
    evidence,
)

assert "definition" in definition_plan.primary_angles

assert definition_plan.generate_flashcards is True

assert "definition" in definition_plan.flashcard_angles

assert definition_plan.recommend_visual is True

assert definition_plan.visual_angle == "definition"

assert definition_plan.include_sources is True

assert definition_plan.include_safety_note is False


# ============================================================
# RISK FACTORS
# ============================================================

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

assert "risk factors" in risk_plan.primary_angles

assert "risk factors" in risk_plan.flashcard_angles

assert risk_plan.include_safety_note is False


# ============================================================
# SYMPTOMS
# ============================================================

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

assert symptom_plan.include_safety_note is True

# Symptoms have no evidence in this fixture.
# Therefore visual support must not be recommended.
assert symptom_plan.recommend_visual is False


# ============================================================
# TREATMENT
# ============================================================

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

assert treatment_plan.include_safety_note is True

assert treatment_plan.primary_angles


# ============================================================
# DIAGNOSIS
# ============================================================

diagnosis_analysis = QueryAnalysis(
    original_question=(
        "How is hypertension diagnosed?"
    ),
    topic="hypertension",
    intent="diagnosis",
)

diagnosis_plan = planner.plan(
    diagnosis_analysis,
    evidence,
)

assert diagnosis_plan.include_safety_note is True

# Diagnosis evidence is missing, so the planner must
# fall back to evidence that actually exists.
assert diagnosis_plan.primary_angles


# ============================================================
# COMPLICATIONS
# ============================================================

complications_analysis = QueryAnalysis(
    original_question=(
        "What complications can hypertension cause?"
    ),
    topic="hypertension",
    intent="complications",
)

complications_plan = planner.plan(
    complications_analysis,
    evidence,
)

assert complications_plan.include_safety_note is True

assert complications_plan.primary_angles


# ============================================================
# GENERAL INFORMATION
# ============================================================

general_analysis = QueryAnalysis(
    original_question=(
        "Tell me about hypertension."
    ),
    topic="hypertension",
    intent="general_information",
)

general_plan = planner.plan(
    general_analysis,
    evidence,
)

assert general_plan.primary_angles

assert general_plan.supporting_angles

assert general_plan.generate_flashcards is True


# ============================================================
# PLAN STRUCTURE
# ============================================================

plans = [
    definition_plan,
    risk_plan,
    symptom_plan,
    treatment_plan,
    diagnosis_plan,
    complications_plan,
    general_plan,
]

for plan in plans:

    assert isinstance(
        plan.primary_angles,
        list,
    )

    assert isinstance(
        plan.supporting_angles,
        list,
    )

    assert isinstance(
        plan.flashcard_angles,
        list,
    )

    assert isinstance(
        plan.generate_flashcards,
        bool,
    )

    assert isinstance(
        plan.include_sources,
        bool,
    )

    assert isinstance(
        plan.include_safety_note,
        bool,
    )

    assert isinstance(
        plan.recommend_visual,
        bool,
    )


# ============================================================
# OUTPUT
# ============================================================

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

print("\nDIAGNOSIS PLAN:")
print("PRIMARY:", diagnosis_plan.primary_angles)
print(
    "SAFETY:",
    diagnosis_plan.include_safety_note,
)

print("\nCOMPLICATIONS PLAN:")
print(
    "PRIMARY:",
    complications_plan.primary_angles,
)
print(
    "SAFETY:",
    complications_plan.include_safety_note,
)

print("\nGENERAL INFORMATION PLAN:")
print(
    "PRIMARY:",
    general_plan.primary_angles,
)
print(
    "SUPPORTING:",
    general_plan.supporting_angles,
)

print("\n" + "=" * 70)
print("STATUS: PASS")
print("=" * 70)