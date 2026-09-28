CardioGuide AI — Backend Specification
1. Problem → Solution Specification
Problem 1 — Cardiovascular information is difficult to understand

Solution: Provide plain-language, structured cardiovascular education adapted to the user's level.

Backend responsibility:

Identify the cardiovascular topic.
Determine the appropriate explanation style.
Provide structured evidence to the response-generation system.
Control response complexity.
Problem 2 — Users have different learning needs

Solution: Personalize explanations and recommendations according to the user's profile, interests, goals, and previous interactions.

Backend responsibility:

Store user preferences.
Track user interests.
Track learning progress.
Build user context for each request.
Problem 3 — Users can lose focus during conversations

Solution: Maintain awareness of the current conversation topic and redirect unrelated questions appropriately.

Backend responsibility:

Track conversation topics.
Detect topic changes.
Determine whether a question is relevant to the current context.
Preserve the user's intended focus.
Problem 4 — Users do not know what to learn next

Solution: Generate context-aware recommendations for useful follow-up topics.

Backend responsibility:

Analyze the current topic.
Identify related knowledge areas.
Consider previous interactions.
Generate relevant recommendations.
Problem 5 — A static interface cannot adapt to the user

Solution: Provide structured backend guidance that allows the frontend to emphasize relevant CardioGuide features.

Backend responsibility:

Determine the user's current focus.
Identify relevant modules.
Recommend relevant learning and support features.
Return structured UI guidance through the API.
Problem 6 — Conversations lack continuity

Solution: Persist conversations and messages so users can continue previous discussions.

Backend responsibility:

Create conversations.
Store messages.
Retrieve conversation history.
Associate conversations with users.
Problem 7 — Follow-up questions can lose context

Solution: Use conversation history and contextual understanding when processing follow-up questions.

Backend responsibility:

Retrieve relevant previous messages.
Maintain conversation context.
Resolve contextual references.
Pass relevant context into the research and response pipeline.
Problem 8 — Users may phrase questions poorly

Solution: Normalize and interpret natural, abbreviated, misspelled, or incomplete questions.

Backend responsibility:

Normalize queries.
Detect intent.
Identify the cardiovascular topic.
Preserve the original user message.
Problem 9 — Medical information needs reliable evidence

Solution: Ground cardiovascular responses in approved medical sources.

Backend responsibility:

Search approved medical sources.
Process retrieved sources.
Build structured evidence packages.
Maintain claim-to-source relationships.
Detect when reliable evidence is unavailable.
Problem 10 — Medical questions require safety boundaries

Solution: Provide cardiovascular education without presenting CardioGuide as a diagnostic or replacement medical-care system.

Backend responsibility:

Detect potentially high-risk requests.
Apply safety rules.
Add appropriate safety guidance.
Escalate appropriate situations toward professional medical care.
Prevent unsupported diagnostic claims.
Problem 11 — Too much information can overwhelm users

Solution: Adapt response length, structure, and complexity to the user's context and needs.

Backend responsibility:

Determine response style.
Use user context.
Use the response planner.
Select appropriate supporting information.
Problem 12 — Reading information does not guarantee learning

Solution: Reinforce learning through flashcards, knowledge checks, recommendations, and progress tracking.

Backend responsibility:

Generate flashcards.
Track learning activities.
Track topics explored.
Track learning progress.
Problem 13 — We need to know whether responses are useful

Solution: Collect lightweight user feedback on CardioGuide responses.

Backend responsibility:

Store feedback.
Associate feedback with users, conversations, and messages.
Make feedback available for product improvement.
Problem 14 — Users may not have a clearly defined goal

Solution: Establish the user's CardioGuide goal during onboarding and use it for personalization.

Backend responsibility:

Store the user's stated goal.
Retrieve the goal during interactions.
Use the goal when generating recommendations.
Use the goal when adapting responses and the user experience.
Problem 15 — The system must know when evidence is insufficient

Solution: Explicitly acknowledge insufficient evidence instead of generating unsupported information.

Backend responsibility:

Detect evidence-retrieval failure.
Preserve evidence status.
Prevent unsupported response generation.
Communicate evidence limitations appropriatel