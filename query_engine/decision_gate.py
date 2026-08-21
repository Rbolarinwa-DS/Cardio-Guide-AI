from dataclasses import dataclass
from typing import Optional


@dataclass
class Decision:
    action: str
    reason: str


class DecisionGate:

    def decide(
        self,
        urgent: bool,
        ambiguous: bool,
        needs_clarification: bool,
        in_scope: bool = True,
    ) -> Decision:

        # Safety takes priority over everything else.
        if urgent:
            return Decision(
                action="urgent_response",
                reason="Potentially urgent symptoms detected."
            )

        # If the question is ambiguous, clarify before retrieval.
        if ambiguous:
            return Decision(
                action="clarify",
                reason="The user's question has multiple possible meanings."
            )

        # If a vague question cannot be resolved from context.
        if needs_clarification:
            return Decision(
                action="clarify",
                reason="There is not enough conversation context to resolve the question."
            )

        # CardioGuide should remain within its intended scope.
        if not in_scope:
            return Decision(
                action="redirect",
                reason="The question is outside CardioGuide's cardiovascular education scope."
            )

        # Normal path.
        return Decision(
            action="proceed",
            reason="Question can proceed to research and response generation."
        )