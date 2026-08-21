from query_engine.cardio_guide import CardioGuide


CSV_PATH = "data/cardioguide_queries.csv"

cardio = CardioGuide(CSV_PATH)


print("=" * 70)
print("CARDIOGUIDE END-TO-END TEST")
print("=" * 70)


# ============================================================
# 1. NORMAL QUESTION
# ============================================================

question = "What is hypertension?"

result = cardio.ask(question)

print("\n" + "=" * 70)
print("NORMAL QUESTION")
print("=" * 70)

print(f"\nQUESTION: {question}")
print(f"ACTION: {result['action']}")

assert result["action"] == "proceed"

assert result["response"]
assert isinstance(result["flashcards"], list)
assert isinstance(result["visual_support"], dict)
assert isinstance(result["sources"], list)

print("\nANSWER:")
print(result["response"])

print("\nFLASHCARDS:")

for index, card in enumerate(
    result["flashcards"],
    start=1,
):
    print(f"\n{index}. {card['question']}")
    print(f"   {card['answer']}")

print("\nVISUAL SUPPORT:")
print(result["visual_support"])

print("\nSOURCES:")

for source in result["sources"]:
    print(
        f"- {source['title']} "
        f"({source['domain']})"
    )


# ============================================================
# 2. VERIFY APPROVED SOURCES
# ============================================================

domains = {
    source["domain"]
    for source in result["sources"]
}

allowed_domains = {
    "who.int",
    "mayoclinic.org",
    "heart.org",
}

assert domains.issubset(
    allowed_domains
)

print("\nAPPROVED SOURCES: PASS")


# ============================================================
# 3. VERIFY EVIDENCE PACKAGE
# ============================================================

assert result["evidence"]

assert (
    result["evidence"].question
    == question
)

assert (
    result["evidence"].combined_evidence
)

assert (
    result["evidence"].evidence_by_angle
)

print("EVIDENCE PACKAGE: PASS")


# ============================================================
# 4. VERIFY RESPONSE PLAN
# ============================================================

assert result["response_plan"]

assert (
    result["response_plan"].primary_angles
)

assert (
    result["response_plan"].generate_flashcards
    is True
)

print("RESPONSE PLAN: PASS")


# ============================================================
# 5. VERIFY VISUAL SUPPORT
# ============================================================

visual = result["visual_support"]

assert "recommended" in visual
assert "angle" in visual
assert "reason" in visual

print("VISUAL SUPPORT STRUCTURE: PASS")


# ============================================================
# 6. VERIFY FLASHCARD STRUCTURE
# ============================================================

for card in result["flashcards"]:

    assert "angle" in card
    assert "question" in card
    assert "answer" in card

    assert card["question"]
    assert card["answer"]


print("FLASHCARD STRUCTURE: PASS")


# ============================================================
# 7. AMBIGUOUS QUESTION
# ============================================================

ambiguous_question = "What causes pressure?"

ambiguous_result = cardio.ask(
    ambiguous_question
)

print("\n" + "=" * 70)
print("AMBIGUOUS QUESTION")
print("=" * 70)

print(
    f"\nQUESTION: {ambiguous_question}"
)

print(
    f"ACTION: {ambiguous_result['action']}"
)

assert (
    ambiguous_result["action"]
    == "clarify"
)

assert ambiguous_result["message"]

print(
    f"MESSAGE: {ambiguous_result['message']}"
)

print("AMBIGUITY HANDLING: PASS")


# ============================================================
# 8. URGENT QUESTION
# ============================================================

urgent_question = (
    "I'm having severe chest pain right now."
)

urgent_result = cardio.ask(
    urgent_question
)

print("\n" + "=" * 70)
print("URGENT QUESTION")
print("=" * 70)

print(
    f"\nQUESTION: {urgent_question}"
)

print(
    f"ACTION: {urgent_result['action']}"
)

assert (
    urgent_result["action"]
    == "urgent_response"
)

assert urgent_result["message"]

print(
    f"MESSAGE: {urgent_result['message']}"
)

print("URGENCY HANDLING: PASS")


# ============================================================
# 9. OUT-OF-SCOPE QUESTION
# ============================================================

out_of_scope_question = (
    "How do I treat my broken leg?"
)

out_of_scope_result = cardio.ask(
    out_of_scope_question
)

print("\n" + "=" * 70)
print("OUT-OF-SCOPE QUESTION")
print("=" * 70)

print(
    f"\nQUESTION: {out_of_scope_question}"
)

print(
    f"ACTION: {out_of_scope_result['action']}"
)

assert (
    out_of_scope_result["action"]
    == "redirect"
)

assert out_of_scope_result["message"]

print(
    f"MESSAGE: {out_of_scope_result['message']}"
)

print("SCOPE HANDLING: PASS")


# ============================================================
# FINAL RESULT
# ============================================================

print("\n" + "=" * 70)
print("CARDIOGUIDE END-TO-END TEST: PASS")
print("=" * 70)