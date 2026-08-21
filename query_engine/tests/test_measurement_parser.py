from query_engine.measurement_parser import MeasurementParser


parser = MeasurementParser()

questions = [
    "My blood pressure is 150/95",
    "BP = 120/80",
    "My LDL is 145 and HDL is 38",
    "LDL = 120 mg/dL",
    "What is hypertension?",
]


for question in questions:

    print("=" * 70)
    print("QUESTION:", question)

    results = parser.parse(question)

    if not results:
        print("MEASUREMENTS: None")
        continue

    print("MEASUREMENTS:")

    for result in results:
        print(
            result.measurement_type,
            result.values,
            result.unit
        )