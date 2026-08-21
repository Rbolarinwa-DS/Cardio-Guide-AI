from dataclasses import dataclass


@dataclass
class ScopeResult:
    in_scope: bool
    topic: str
    confidence: float


class ScopeClassifier:

    CARDIOVASCULAR_TOPICS = {
        "hypertension",
        "blood pressure",
        "cholesterol",
        "ldl",
        "hdl",
        "heart",
        "cardiovascular",
        "heart attack",
        "coronary artery disease",
        "heart failure",
        "arrhythmia",
        "atrial fibrillation",
        "atherosclerosis",
        "stroke",
        "rheumatic heart disease",
        "blood vessels",
        "medication",
        "statin",
        "cardiovascular health",
        "heart health",
    }

    def classify(self, question: str) -> ScopeResult:
        text = question.lower().strip()

        for topic in self.CARDIOVASCULAR_TOPICS:
            if topic in text:
                return ScopeResult(
                    in_scope=True,
                    topic=topic,
                    confidence=0.95,
                )

        return ScopeResult(
            in_scope=False,
            topic="unknown",
            confidence=0.90,
        )