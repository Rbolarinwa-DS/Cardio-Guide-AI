from query_engine.intent_classifier import IntentClassifier


classifier = IntentClassifier()

questions = [
    "What is hypertension?",
    "What are the symptoms of hypertension?",
    "What causes hypertension?",
    "How is hypertension treated?",
    "What are the side effects of statins?",
    "What's the difference between LDL and HDL?",
    "Why?",
    "Tell me something about hypertension.",
]


for question in questions:
    result = classifier.classify(question)

    print("=" * 70)
    print("QUESTION:", question)
    print("INTENT:", result.intent)
    print("CONFIDENCE:", result.confidence)