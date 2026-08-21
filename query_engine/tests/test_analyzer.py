from query_engine.analyzer import QueryAnalyzer


CSV_PATH = "data/cardioguide_queries.csv"


analyzer = QueryAnalyzer(CSV_PATH)


questions = [
    "What is hypertension?",
    "Explain hypertension in detail",
    "What is blood pressure?",
    "What are statins?",
    "What foods are good for heart health?",
    "Tell me something about hypertension that isn't in the dataset."
]


for question in questions:

    result = analyzer.analyze(question)

    print("=" * 60)
    print("QUESTION:", question)
    print(result)
    