from dataclasses import dataclass


@dataclass
class SemanticQuery:
    original_question: str
    topic: str | None
    subtopic: str | None
    intent: str | None
    explicit_depth: str | None
    knowledge_level: str | None
    user_goal: str | None
    response_strategy: str | None
    visual_support: str | None
    confidence: float


def analyze_semantically(question: str) -> SemanticQuery:
    """
    Temporary Phase 1 semantic analyzer.

    This is intentionally rule-based for now.
    The research engine will later replace/augment this
    with an actual semantic/LLM-based classifier.
    """

    q = question.lower().strip()

    topic = None
    subtopic = None
    intent = None
    explicit_depth = None
    knowledge_level = None
    user_goal = None
    response_strategy = None
    visual_support = "recommended"

    # -------------------------
    # Topic detection
    # -------------------------

    if any(word in q for word in [
        "hypertension",
        "high blood pressure",
        "blood pressure"
    ]):
        topic = "Hypertension"

        if "blood pressure" in q and "hypertension" not in q:
            subtopic = "Blood Pressure"
        else:
            subtopic = "General"

    elif any(word in q for word in [
        "cholesterol",
        "ldl",
        "hdl"
    ]):
        topic = "Cholesterol"

    elif any(word in q for word in [
        "statin",
        "beta blocker",
        "ace inhibitor",
        "arb",
        "anticoagulant",
        "antiplatelet",
        "diuretic",
        "medication",
        "medicine",
        "drug"
    ]):
        topic = "Medications"

    elif any(word in q for word in [
        "heart attack",
        "myocardial infarction"
    ]):
        topic = "Heart Attack"

    elif "heart failure" in q:
        topic = "Heart Failure"

    elif any(word in q for word in [
        "arrhythmia",
        "atrial fibrillation",
        "afib"
    ]):
        topic = "Arrhythmia"

    elif "atherosclerosis" in q:
        topic = "Atherosclerosis"

    elif "rheumatic heart disease" in q:
        topic = "Rheumatic Heart Disease"

    elif "stroke" in q:
        topic = "Stroke Prevention"

    elif any(word in q for word in [
        "exercise",
        "diet",
        "food",
        "smoking",
        "sleep",
        "stress"
    ]):
        topic = "Lifestyle"

    # -------------------------
    # Intent detection
    # -------------------------

    if any(phrase in q for phrase in [
        "what is",
        "what are",
        "what's",
        "define"
    ]):
        intent = "definition"

    elif any(phrase in q for phrase in [
        "how does",
        "how do",
        "why does",
        "why do",
        "how is"
    ]):
        intent = "explanation"

    elif any(word in q for word in [
        "cause",
        "causes",
        "caused",
        "risk factor"
    ]):
        intent = "causes"

    elif any(word in q for word in [
        "symptom",
        "symptoms",
        "warning sign"
    ]):
        intent = "symptoms"

    elif any(word in q for word in [
        "prevent",
        "prevention",
        "reduce my risk"
    ]):
        intent = "prevention"

    elif any(word in q for word in [
        "side effect",
        "side effects"
    ]):
        intent = "side_effects"

    elif any(word in q for word in [
        "difference",
        "compare",
        "versus",
        "vs"
    ]):
        intent = "comparison"

    # -------------------------
    # Explicit depth
    # -------------------------

    if any(phrase in q for phrase in [
        "3-4 lines",
        "3 lines",
        "4 lines",
        "briefly",
        "in short",
        "short answer"
    ]):
        explicit_depth = "short"

    elif any(phrase in q for phrase in [
        "basic",
        "simply",
        "simple terms",
        "simple explanation"
    ]):
        explicit_depth = "basic"

    elif any(phrase in q for phrase in [
        "in detail",
        "detailed",
        "deep",
        "deeply"
    ]):
        explicit_depth = "detailed"

    elif any(phrase in q for phrase in [
        "everything",
        "complete guide",
        "teach me",
        "full explanation",
        "comprehensive"
    ]):
        explicit_depth = "comprehensive"

    # -------------------------
    # Knowledge level
    # -------------------------

    if any(phrase in q for phrase in [
        "i don't know anything",
        "i know nothing",
        "i'm new to this",
        "new to biology",
        "beginner"
    ]):
        knowledge_level = "beginner"

    # -------------------------
    # User goal
    # -------------------------

    if any(word in q for word in [
        "teach",
        "learn",
        "explain",
        "understand"
    ]):
        user_goal = "learn_topic"

    elif any(word in q for word in [
        "prevent",
        "reduce risk"
    ]):
        user_goal = "prevent_disease"

    elif any(word in q for word in [
        "medicine",
        "medication",
        "drug"
    ]):
        user_goal = "understand_medication"

    else:
        user_goal = "understand_concept"

    # -------------------------
    # Response strategy
    # -------------------------

    if explicit_depth == "short":
        response_strategy = "strict_concise_explanation"

    elif explicit_depth == "basic":
        response_strategy = "beginner_explanation"

    elif explicit_depth == "detailed":
        response_strategy = "detailed_explanation"

    elif explicit_depth == "comprehensive":
        response_strategy = "comprehensive_learning_guide"

    elif topic == "Medications":
        response_strategy = "adaptive_drug_explanation"

    else:
        response_strategy = "adaptive_beginner_explanation"

    # -------------------------
    # Confidence
    # -------------------------

    signals = sum([
        topic is not None,
        intent is not None,
        explicit_depth is not None,
        knowledge_level is not None
    ])

    confidence = signals / 4

    return SemanticQuery(
        original_question=question,
        topic=topic,
        subtopic=subtopic,
        intent=intent,
        explicit_depth=explicit_depth,
        knowledge_level=knowledge_level,
        user_goal=user_goal,
        response_strategy=response_strategy,
        visual_support=visual_support,
        confidence=round(confidence, 2)
    )