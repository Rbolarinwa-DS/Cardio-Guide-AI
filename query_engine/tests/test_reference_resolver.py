from query_engine.context_manager import ContextManager
from query_engine.reference_resolver import ReferenceResolver


context = ContextManager()

context.add_turn(
    question="What are the symptoms of hypertension?",
    answer="Hypertension can often have no obvious symptoms.",
    topic="Hypertension"
)

resolver = ReferenceResolver(context)

questions = [
    "Can it cause headaches?",
    "How is it treated?",
    "What about medication?",
    "Why?",
]

for question in questions:
    result = resolver.resolve(question)

    print("=" * 70)
    print("ORIGINAL:", result.original_question)
    print("RESOLVED:", result.resolved_question)
    print("ACTIVE TOPIC:", result.active_topic)
    print("NEEDS CLARIFICATION:", result.needs_clarification)