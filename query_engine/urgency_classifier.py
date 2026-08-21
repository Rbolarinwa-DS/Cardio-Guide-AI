from dataclasses import dataclass


@dataclass
class UrgencyResult:
    level: str
    urgent: bool
    matched_signals: list[str]


class UrgencyClassifier:

    URGENT_PATTERNS = {
        "chest_pain": [
            "severe chest pain",
            "crushing chest pain",
            "chest pain right now",
            "heavy pain in my chest",
            "pressure in my chest",
        ],

        "breathing": [
            "difficulty breathing",
            "can't breathe",
            "cannot breathe",
            "struggling to breathe",
            "shortness of breath",
        ],

        "fainting": [
            "fainting",
            "fainted",
            "passed out",
            "about to pass out",
        ],

        "stroke_signs": [
            "face drooping",
            "my face is drooping",
            "slurred speech",
            "my speech is slurred",
            "speech is slurred",
            "sudden weakness",
            "sudden numbness",
        ],
    }

    def classify(self, question: str) -> UrgencyResult:

        text = question.lower().strip()

        matched_signals = []

        for category, patterns in self.URGENT_PATTERNS.items():

            for pattern in patterns:

                if pattern in text:
                    matched_signals.append(category)
                    break

        if matched_signals:

            return UrgencyResult(
                level="urgent",
                urgent=True,
                matched_signals=matched_signals,
            )

        return UrgencyResult(
            level="normal",
            urgent=False,
            matched_signals=[],
        )