from query_engine.ambiguity_detector import AmbiguityDetector

detector = AmbiguityDetector()

questions = [
    "What causes pressure?",
    "What is hypertension?",
    "Can pressure be dangerous?",
    "What is blood pressure?",
    "What is chest pressure?",
    "What is hypertension?",
    "What is a heart attack?",
    "What is heart failure?",
    "What does failure mean?",
]


for question in questions:

    result = detector.detect(question)

    print("=" * 70)
    print("QUESTION:", question)
    print("AMBIGUOUS:", result.ambiguous)

    if result.ambiguous:
        print("TERM:", result.term)
        print("MEANINGS:", result.possible_meanings)
        print("CLARIFICATION:", result.clarification_question)