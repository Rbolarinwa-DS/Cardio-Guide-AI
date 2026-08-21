from query_engine.context_manager import ContextManager
from query_engine.topic_tracker import TopicTracker


context = ContextManager()

context.update_user_context(
    condition="Hypertension"
)

tracker = TopicTracker(context)


questions = [
    ("Can hypertension cause headaches?", "Hypertension"),
    ("What medications are commonly used?", "Hypertension"),
    ("Actually, what is cholesterol?", "Cholesterol"),
]

for question, detected_topic in questions:

    result = tracker.detect(
        question=question,
        detected_topic=detected_topic
    )

    print("=" * 70)
    print("QUESTION:", question)
    print("ACTIVE TOPIC:", context.get_active_topic())
    print("DETECTED TOPIC:", result.topic)
    print("TOPIC SWITCHED:", result.switched)

    tracker.update(result.topic)
    