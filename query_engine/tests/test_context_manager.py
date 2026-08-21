from query_engine.context_manager import ContextManager


context = ContextManager()

context.update_user_context(
    knowledge_level="beginner",
    user_goal="understand_concept",
    condition="Hypertension"
)

context.add_turn(
    question="What is hypertension?",
    answer="Hypertension is high blood pressure.",
    topic="Hypertension"
)

print("ACTIVE TOPIC:", context.get_active_topic())

last_turn = context.get_last_turn()

print("LAST QUESTION:", last_turn.question)
print("LAST ANSWER:", last_turn.answer)

print("\nUSER CONTEXT:")
print("Knowledge:", context.user_context.knowledge_level)
print("Goal:", context.user_context.user_goal)
print("Condition:", context.user_context.condition)
