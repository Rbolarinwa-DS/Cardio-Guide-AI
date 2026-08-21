import re
from dataclasses import dataclass


@dataclass
class PreprocessedQuery:
    original: str
    corrected: str
    abbreviations_expanded: bool


class QueryPreprocessor:

    ABBREVIATIONS = {
        "bp": "blood pressure",
        "b.p.": "blood pressure",
        "hr": "heart rate",
        "ldl": "low-density lipoprotein",
        "hdl": "high-density lipoprotein",
        "af": "atrial fibrillation",
        "afib": "atrial fibrillation",
        "cad": "coronary artery disease",
        "chf": "congestive heart failure",
        "mi": "heart attack",
    }

    CORRECTIONS = {
        "hypertention": "hypertension",
        "hypertenson": "hypertension",
        "hipertension": "hypertension",
        "cholestrol": "cholesterol",
        "cholestrol": "cholesterol",
        "arhythmia": "arrhythmia",
        "arrythmia": "arrhythmia",
        "medecine": "medicine",
    }

    def preprocess(self, question: str) -> PreprocessedQuery:
        corrected = question.strip()

        corrected = re.sub(r"\s+", " ", corrected)

        corrected = self._correct_common_typos(corrected)

        expanded = False

        for abbreviation, meaning in self.ABBREVIATIONS.items():
            pattern = rf"\b{re.escape(abbreviation)}\b"

            if re.search(pattern, corrected, flags=re.IGNORECASE):
                corrected = re.sub(
                    pattern,
                    meaning,
                    corrected,
                    flags=re.IGNORECASE
                )
                expanded = True

        return PreprocessedQuery(
            original=question,
            corrected=corrected,
            abbreviations_expanded=expanded,
        )

    def _correct_common_typos(self, text: str) -> str:
        for typo, correction in self.CORRECTIONS.items():
            pattern = rf"\b{re.escape(typo)}\b"

            text = re.sub(
                pattern,
                correction,
                text,
                flags=re.IGNORECASE
            )

        return text