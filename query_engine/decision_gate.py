from dataclasses import dataclass


@dataclass
class Decision:
    action: str
    reason: str


class DecisionGate:
    """
    Central routing decision for CardioGuide.

    Priority:

        1. Urgent medical situation
        2. Security / privacy-sensitive request
        3. High-risk personalized medical treatment
        4. Ambiguity
        5. Missing clarification
        6. Scope
        7. Normal generation

    Emergency routing deliberately has the highest priority.
    """

    def decide(
        self,
        urgent: bool,
        ambiguous: bool,
        needs_clarification: bool,
        in_scope: bool = True,
        security_sensitive: bool = False,
        high_risk_medical: bool = False,
    ) -> Decision:

        # ========================================================
        # 1. URGENT
        # ========================================================

        if urgent:
            return Decision(
                action="urgent_response",
                reason=(
                    "Potentially urgent symptoms were detected. "
                    "Emergency guidance takes priority over "
                    "ambiguity, scope, and normal generation."
                ),
            )

        # ========================================================
        # 2. SECURITY / INTERNAL INFORMATION
        # ========================================================

        if security_sensitive:
            return Decision(
                action="security_response",
                reason=(
                    "The request attempts to obtain internal, "
                    "private, confidential, or implementation "
                    "information."
                ),
            )

        # ========================================================
        # 3. HIGH-RISK MEDICAL TREATMENT
        # ========================================================

        if high_risk_medical:
            return Decision(
                action="high_risk_medical",
                reason=(
                    "The request asks for individualized medical "
                    "treatment, medication, dosage, or treatment "
                    "changes that CardioGuide should not prescribe."
                ),
            )

        # ========================================================
        # 4. AMBIGUITY
        # ========================================================

        if ambiguous:
            return Decision(
                action="clarify",
                reason=(
                    "The user's question contains a term with "
                    "multiple plausible meanings."
                ),
            )

        # ========================================================
        # 5. MISSING CONTEXT
        # ========================================================

        if needs_clarification:
            return Decision(
                action="clarify",
                reason=(
                    "There is not enough conversation context "
                    "to safely resolve the question."
                ),
            )

        # ========================================================
        # 6. OUT OF SCOPE
        # ========================================================

        if not in_scope:
            return Decision(
                action="redirect",
                reason=(
                    "The question is outside CardioGuide's "
                    "cardiovascular health education scope."
                ),
            )

        # ========================================================
        # 7. NORMAL
        # ========================================================

        return Decision(
            action="proceed",
            reason=(
                "Question can proceed to evidence retrieval "
                "and response generation."
            ),
        )