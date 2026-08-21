from query_engine.analyzer import QueryAnalyzer
from query_engine.fallback import apply_fallback


CSV_PATH = "data/cardioguide_queries.csv"

analyzer = QueryAnalyzer(CSV_PATH)


questions = [
    "What is hypertension?",
    "Tell me something about hypertension that isn't in the dataset.",
]


for question in questions:

    analysis = analyzer.analyze(question)

    print("=" * 70)
    print("QUESTION:", question)

    print("\nBEFORE FALLBACK:")
    print(analysis)

    result = apply_fallback(analysis)

    print("\nAFTER FALLBACK:")
    print(result)