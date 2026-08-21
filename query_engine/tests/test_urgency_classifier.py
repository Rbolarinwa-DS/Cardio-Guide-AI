from query_engine.urgency_classifier import UrgencyClassifier


classifier = UrgencyClassifier()

questions = [
    "What is chest pain?",
    "I'm having severe chest pain right now.",
    "I can't breathe and I'm feeling faint.",
    "My face is drooping and my speech is slurred.",
    "My speech suddenly became slurred.",
    "One side of my face is drooping.",
    "I suddenly have weakness in my arm.",
    "What are the symptoms of hypertension?",
]


for question in questions:

    result = classifier.classify(question)

    print("=" * 70)
    print("QUESTION:", question)
    print("LEVEL:", result.level)
    print("URGENT:", result.urgent)
    print("SIGNALS:", result.matched_signals)