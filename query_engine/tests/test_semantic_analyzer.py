from query_engine.semantic_analyzer import analyze_semantically


questions = [
    "What is hypertension?",
    "Explain hypertension in detail",
    "What medications can affect blood pressure?",
    "Can high blood pressure damage the kidneys?",
    "Why does my blood pressure change during the day?",
    "I don't know anything about cholesterol. Teach me.",
    "What happens if I take two blood pressure medicines together?",
    "Explain blood pressure like I'm completely new to biology.",
    "Give me 3-4 lines about hypertension.",
    "Tell me something about hypertension that isn't in the dataset.",
]


for question in questions:
    result = analyze_semantically(question)

    print("=" * 70)
    print("QUESTION:", question)
    print(result)