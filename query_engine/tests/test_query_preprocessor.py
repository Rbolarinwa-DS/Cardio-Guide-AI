from query_engine.query_preprocessor import QueryPreprocessor


preprocessor = QueryPreprocessor()

questions = [
    "What is hypertention?",
    "wat is high bp?",
    "Is my LDL bad?",
    "What is AF?",
    "What is cholestrol?",
    "  Explain   hypertension  ",
]

for question in questions:
    result = preprocessor.preprocess(question)

    print("=" * 70)
    print("ORIGINAL:", result.original)
    print("CORRECTED:", result.corrected)
    print(
        "ABBREVIATIONS EXPANDED:",
        result.abbreviations_expanded
    )
    