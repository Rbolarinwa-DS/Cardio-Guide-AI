from query_engine.matcher import QueryMatcher


CSV_PATH = "data/cardioguide_queries.csv"

matcher = QueryMatcher(CSV_PATH)


questions = [
    "What is hypertension?",
    "Explain hypertension in detail",
    "What is high blood pressure?",
    "How does hypertension affect the heart?",
    "Can high blood pressure damage my kidneys?",
    "What medications can affect blood pressure?"
]


for question in questions:
    result = matcher.match(question)

    print("=" * 70)
    print("QUESTION:", question)

    if result:
        print("MATCH FOUND")
        print("Query ID:", result["query_id"])
        print("Matched question:", result["matched_question"])
        print("Similarity:", result["similarity"])
        print("Topic:", result["topic"])
        print("Intent:", result["intent"])
    else:
        print("NO CONFIDENT MATCH")
        