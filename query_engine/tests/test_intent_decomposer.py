from query_engine.intent_decomposer import IntentDecomposer


decomposer = IntentDecomposer()

questions = [
    "What is hypertension, what causes it, can it be cured and what should I eat?",
    "What is hypertension?",
    "What causes high blood pressure and how is it treated?",
]


for question in questions:

    print("=" * 70)
    print("ORIGINAL:")
    print(question)

    sub_questions = decomposer.decompose(question)

    print("\nSUB-QUESTIONS:")

    for item in sub_questions:
        print(f"{item.position}. {item.question}")