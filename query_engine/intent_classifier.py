from dataclasses import dataclass


@dataclass
class IntentResult:
    intent: str
    confidence: float


class IntentClassifier:

    def classify(self, question: str) -> IntentResult:
        text = question.lower().strip()

        if self._is_comparison(text):
            return IntentResult("comparison", 0.95)

        if self._is_side_effects(text):
            return IntentResult("side_effects", 0.95)

        if self._is_treatment(text):
            return IntentResult("treatment", 0.90)

        if self._is_symptoms(text):
            return IntentResult("symptoms", 0.90)

        if self._is_risk_factors(text):
            return IntentResult("risk_factors", 0.90)

        if self._is_definition(text):
            return IntentResult("definition", 0.90)

        if self._is_follow_up(text):
            return IntentResult("follow_up", 0.85)

        return IntentResult("general_information", 0.50)

    def _is_comparison(self, text: str) -> bool:
        return (
            "difference between" in text
            or "difference in" in text
            or "compare" in text
            or "versus" in text
            or " vs " in text
        )

    def _is_side_effects(self, text: str) -> bool:
        return (
            "side effect" in text
            or "side effects" in text
            or "adverse effect" in text
            or "adverse effects" in text
        )

    def _is_treatment(self, text: str) -> bool:
        return (
            "how is it treated" in text
            or "how is" in text and "treated" in text
            or "treatment" in text
            or "how to treat" in text
        )

    def _is_symptoms(self, text: str) -> bool:
        return (
            "symptom" in text
            or "signs of" in text
            or "what does it feel like" in text
        )

    def _is_risk_factors(self, text: str) -> bool:
        return (
            "risk factor" in text
            or "causes" in text
            or "cause of" in text
            or "what increases" in text
        )

    def _is_definition(self, text: str) -> bool:
        return (
            text.startswith("what is ")
            or text.startswith("what are ")
            or text.startswith("define ")
            or text.startswith("what does ") and text.endswith(" mean?")
        )

    def _is_follow_up(self, text: str) -> bool:
        return text in {
            "why?",
            "how?",
            "what about that?",
            "explain that",
            "tell me more",
            "give me an example",
        }