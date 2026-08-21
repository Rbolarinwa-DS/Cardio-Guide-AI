from query_engine.decision_gate import DecisionGate


gate = DecisionGate()


tests = [
    {
        "name": "Normal question",
        "urgent": False,
        "ambiguous": False,
        "needs_clarification": False,
        "in_scope": True,
    },
    {
        "name": "Urgent symptoms",
        "urgent": True,
        "ambiguous": False,
        "needs_clarification": False,
        "in_scope": True,
    },
    {
        "name": "Ambiguous question",
        "urgent": False,
        "ambiguous": True,
        "needs_clarification": False,
        "in_scope": True,
    },
    {
        "name": "Vague question",
        "urgent": False,
        "ambiguous": False,
        "needs_clarification": True,
        "in_scope": True,
    },
    {
        "name": "Outside scope",
        "urgent": False,
        "ambiguous": False,
        "needs_clarification": False,
        "in_scope": False,
    },
]


for test in tests:

    result = gate.decide(
        urgent=test["urgent"],
        ambiguous=test["ambiguous"],
        needs_clarification=test["needs_clarification"],
        in_scope=test["in_scope"],
    )

    print("=" * 70)
    print("TEST:", test["name"])
    print("ACTION:", result.action)
    print("REASON:", result.reason)