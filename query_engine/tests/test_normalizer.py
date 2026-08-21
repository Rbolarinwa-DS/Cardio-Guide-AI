from query_engine.normalizer import normalize_query


test_questions = [
    "WHAT is hypertension??",
    "what's high blood pressure",
    "Can u tell me what high BP is?",
    "  Explain   hypertension   ",
    "I'm new to this, what's hypertension?"
]


for question in test_questions:
    print("Original :", question)
    print("Normalized:", normalize_query(question))
    print("-" * 50)