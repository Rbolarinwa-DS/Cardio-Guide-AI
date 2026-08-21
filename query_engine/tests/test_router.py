from query_engine.analyzer import QueryAnalyzer
from query_engine.router import QueryRouter


CSV_PATH = "data/cardioguide_queries.csv"

analyzer = QueryAnalyzer(CSV_PATH)
router = QueryRouter()


questions = [
    "What is hypertension?",
    "Tell me something about hypertension that isn't in the dataset.",
]


for question in questions:

    analysis = analyzer.analyze(question)
    result = router.route(analysis)

    print("=" * 70)
    print("QUESTION:", question)
    print("\nROUTE:", result["route"])
    print("RESEARCH REQUIRED:", result["research_required"])
    print("SOURCE COUNT:", result["source_count"])
    print("\nANALYSIS:")
    print(result["analysis"])