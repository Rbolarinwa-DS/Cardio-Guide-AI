from query_engine.scope_classifier import ScopeClassifier


classifier = ScopeClassifier()

questions = [
    "What is hypertension?",
    "What does LDL mean?",
    "What causes heart failure?",
    "What foods are good for heart health?",
    "What is atrial fibrillation?",
    "How do I treat a broken leg?",
    "How do I fix my laptop?",
]


for question in questions:

    result = classifier.classify(question)

    print("=" * 70)
    print("QUESTION:", question)
    print("IN SCOPE:", result.in_scope)
    print("TOPIC:", result.topic)
    print("CONFIDENCE:", result.confidence)