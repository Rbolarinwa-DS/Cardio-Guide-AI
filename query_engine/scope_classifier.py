"""
CardioGuide AI — Scope Classifier

Determines whether a user query belongs within CardioGuide's supported domain.

Design principles:
- Scope classification is routing, not diagnosis.
- Do not infer a specific cardiovascular disease from a generic symptom.
- Support common medical abbreviations and contextual shorthand.
- Distinguish medical abbreviations from non-medical uses where practical.
- Preserve the original user query.
- Do not rewrite or normalize user-facing text.
- Technical/software requests remain out of scope unless they are clearly
  asking a cardiovascular-health question.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------

@dataclass
class ScopeResult:
    in_scope: bool
    scope: str
    reason: str
    confidence: float
    matched_terms: List[str]


# ---------------------------------------------------------------------------
# Cardiovascular topic vocabulary
# ---------------------------------------------------------------------------

CARDIOVASCULAR_TOPICS: Dict[str, List[str]] = {
    "hypertension": [
        "hypertension",
        "high blood pressure",
        "high bp",
        "blood pressure",
        "blood pressure reading",
        "blood pressure readings",
        "htn",
        "bp",
    ],
    "cholesterol": [
        "cholesterol",
        "high cholesterol",
        "ldl",
        "hdl",
        "triglycerides",
        "triglyceride",
    ],
    "coronary_artery_disease": [
        "coronary artery disease",
        "coronary heart disease",
        "cad",
    ],
    "heart_attack": [
        "heart attack",
        "myocardial infarction",
        "mi",
        "m.i.",
    ],
    "heart_failure": [
        "heart failure",
        "congestive heart failure",
        "chf",
        "hf",
    ],
    "atrial_fibrillation": [
        "atrial fibrillation",
        "afib",
        "a-fib",
        "a fib",
        "af",
    ],
    "arrhythmia": [
        "arrhythmia",
        "arrhythmias",
        "irregular heartbeat",
        "irregular heart beat",
        "abnormal heart rhythm",
        "heart rhythm",
    ],
    "atherosclerosis": [
        "atherosclerosis",
        "artery blockage",
        "blocked arteries",
        "plaque buildup",
        "plaque build up",
    ],
    "stroke": [
        "stroke",
        "stroke prevention",
        "ischemic stroke",
        "haemorrhagic stroke",
        "hemorrhagic stroke",
    ],
    "rheumatic_heart_disease": [
        "rheumatic heart disease",
        "rhd",
    ],
    "cardiovascular_health": [
        "cardiovascular health",
        "cardiovascular disease",
        "cardiovascular diseases",
        "heart health",
        "heart problems",
        "heart condition",
        "heart conditions",
        "cardiac health",
        "cardiac disease",
        "cardiac diseases",
    ],
}


# ---------------------------------------------------------------------------
# Cardiovascular symptoms
# ---------------------------------------------------------------------------

CARDIOVASCULAR_SYMPTOMS: List[str] = [
    "chest pain",
    "chest pressure",
    "chest tightness",
    "chest discomfort",
    "chest heaviness",
    "heart pain",
    "shortness of breath",
    "difficulty breathing",
    "trouble breathing",
    "breathlessness",
    "sob",
    "palpitations",
    "heart palpitations",
    "racing heart",
    "heart racing",
    "rapid heartbeat",
    "fast heartbeat",
    "irregular heartbeat",
    "irregular heart beat",
    "dizziness",
    "fainting",
    "passing out",
    "swollen legs",
    "swollen leg",
    "leg swelling",
    "ankle swelling",
    "swollen ankles",
    "swollen feet",
    "foot swelling",
    "fluid retention",
    "unusual fatigue",
    "extreme fatigue",
]


# ---------------------------------------------------------------------------
# General cardiovascular context
# ---------------------------------------------------------------------------

CARDIOVASCULAR_CONTEXT: List[str] = [
    "heart",
    "cardiac",
    "cardiovascular",
    "blood pressure",
    "bp",
    "hypertension",
    "htn",
    "cholesterol",
    "ldl",
    "hdl",
    "triglycerides",
    "artery",
    "arteries",
    "vein",
    "circulation",
    "heartbeat",
    "heart beat",
    "heart rate",
    "pulse",
    "cardio",
    "cardiovascular system",
]


# ---------------------------------------------------------------------------
# Broader medical context
# ---------------------------------------------------------------------------

MEDICAL_CONTEXT: List[str] = [
    "symptom",
    "symptoms",
    "disease",
    "condition",
    "diagnosis",
    "diagnosed",
    "diagnose",
    "treatment",
    "medication",
    "medicine",
    "drug",
    "doctor",
    "hospital",
    "clinic",
    "patient",
    "medical",
    "health",
    "healthcare",
    "risk factor",
    "risk factors",
    "side effect",
    "side effects",
    "emergency",
    "urgent",
    "blood test",
    "lab test",
    "scan",
    "ecg",
    "ekg",
    "echocardiogram",
]


# ---------------------------------------------------------------------------
# Generic symptom language
# ---------------------------------------------------------------------------

GENERIC_SYMPTOMS: List[str] = [
    "pain",
    "ache",
    "aches",
    "swelling",
    "swollen",
    "weak",
    "weakness",
    "tired",
    "fatigue",
    "dizzy",
    "dizziness",
    "faint",
    "fainting",
    "breathless",
    "breathing",
    "breath",
    "sweating",
    "sweaty",
    "nausea",
    "vomiting",
    "headache",
    "blurred vision",
    "blurry vision",
    "vision changes",
    "palpitations",
    "racing",
    "beating fast",
    "beating quickly",
]


# ---------------------------------------------------------------------------
# Technical / software vocabulary
# ---------------------------------------------------------------------------

TECHNICAL_TERMS: List[str] = [
    "python",
    "javascript",
    "typescript",
    "java",
    "c++",
    "c#",
    "sql",
    "html",
    "css",
    "react",
    "nextjs",
    "next.js",
    "node",
    "nodejs",
    "fastapi",
    "django",
    "flask",
    "api",
    "rest api",
    "graphql",
    "database",
    "postgresql",
    "mysql",
    "mongodb",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "github",
    "git",
    "repository",
    "repo",
    "server",
    "backend",
    "frontend",
    "deployment",
    "deploy",
    "programming",
    "coding",
    "code",
    "software",
    "website",
    "web app",
    "mobile app",
    "application",
    "algorithm",
    "machine learning",
    "deep learning",
    "neural network",
    "model training",
    "debug",
    "debugging",
    "compile",
    "compiler",
    "terminal",
    "powershell",
    "command line",
]


TECHNICAL_ACTIONS: List[str] = [
    "write code",
    "write a script",
    "build an app",
    "build a website",
    "build an api",
    "create an api",
    "create a database",
    "deploy",
    "debug",
    "fix my code",
    "fix this code",
    "install",
    "configure",
    "setup",
    "set up",
    "program",
    "implement",
    "refactor",
    "integrate",
    "connect",
    "run this code",
    "run the code",
]


TECHNICAL_DOMAINS: List[str] = [
    "software development",
    "web development",
    "app development",
    "backend development",
    "frontend development",
    "data science",
    "machine learning",
    "artificial intelligence",
    "devops",
    "cybersecurity",
    "programming",
]


# ---------------------------------------------------------------------------
# Medical abbreviation handling
# ---------------------------------------------------------------------------

STRONG_MEDICAL_ABBREVIATIONS: Dict[str, str] = {
    "chf": "heart failure",
    "htn": "hypertension",
    "bp": "blood pressure",
    "sob": "shortness of breath",
    "afib": "atrial fibrillation",
    "a-fib": "atrial fibrillation",
    "a fib": "atrial fibrillation",
    "mi": "heart attack",
    "m.i.": "heart attack",
    "cad": "coronary artery disease",
    "rhd": "rheumatic heart disease",
}


CONTEXT_DEPENDENT_ABBREVIATIONS: Dict[str, str] = {
    "hf": "heart failure",
    "af": "atrial fibrillation",
}


# ---------------------------------------------------------------------------
# Context cues for ambiguous abbreviations
# ---------------------------------------------------------------------------

MEDICAL_QUERY_CUES: List[str] = [
    "symptom",
    "symptoms",
    "sign",
    "signs",
    "cause",
    "causes",
    "risk",
    "risk factor",
    "risk factors",
    "diagnosis",
    "diagnosed",
    "treatment",
    "treat",
    "medication",
    "medicine",
    "disease",
    "condition",
    "heart",
    "cardiac",
    "cardiovascular",
    "blood",
    "pressure",
    "stroke",
    "chest",
    "breathing",
    "breath",
    "shortness",
    "palpitation",
    "heartbeat",
    "rhythm",
    "swelling",
    "legs",
    "ankles",
    "doctor",
    "hospital",
    "medical",
    "health",
    "patient",
    "urgent",
    "emergency",
    "complication",
    "complications",
    "prevent",
    "prevention",
    "monitor",
    "monitoring",
]


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------

class ScopeClassifier:
    """
    Classifies queries into:
        - in_scope
        - out_of_scope

    The classifier deliberately avoids diagnosing the user.
    """

    def __init__(self) -> None:
        self.cardio_topics = CARDIOVASCULAR_TOPICS
        self.cardio_symptoms = CARDIOVASCULAR_SYMPTOMS
        self.cardio_context = CARDIOVASCULAR_CONTEXT
        self.medical_context = MEDICAL_CONTEXT
        self.generic_symptoms = GENERIC_SYMPTOMS

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def classify(self, query: str) -> ScopeResult:
        """
        Classify a raw or normalized user query.

        Returns a ScopeResult rather than raising for ordinary malformed
        input.
        """

        if not isinstance(query, str):
            return ScopeResult(
                in_scope=False,
                scope="out_of_scope",
                reason="Invalid query type.",
                confidence=1.0,
                matched_terms=[],
            )

        text = self._clean_text(query)

        if not text:
            return ScopeResult(
                in_scope=False,
                scope="out_of_scope",
                reason="Empty query.",
                confidence=1.0,
                matched_terms=[],
            )

        # Technical requests must be checked first.
        technical_result = self._classify_technical_request(text)
        if technical_result is not None:
            return technical_result

        # 1. Explicit cardiovascular disease/topic.
        topic_result = self._classify_explicit_topic(text)
        if topic_result is not None:
            return topic_result

        # 2. Explicit cardiovascular symptom.
        symptom_result = self._classify_cardio_symptom(text)
        if symptom_result is not None:
            return symptom_result

        # 3. Generic symptom with cardiovascular/medical context.
        contextual_symptom_result = self._classify_contextual_symptom(text)
        if contextual_symptom_result is not None:
            return contextual_symptom_result

        # 4. Heart/cardiovascular context with medical language.
        medical_cardio_result = self._classify_medical_cardio_context(text)
        if medical_cardio_result is not None:
            return medical_cardio_result

        # 5. Explicit cardiovascular-health language.
        health_result = self._classify_general_health_context(text)
        if health_result is not None:
            return health_result

        return ScopeResult(
            in_scope=False,
            scope="out_of_scope",
            reason="The query does not contain sufficient cardiovascular or medical context.",
            confidence=0.90,
            matched_terms=[],
        )

    def is_in_scope(self, query: str) -> bool:
        """Convenience method returning only the boolean scope decision."""
        return self.classify(query).in_scope

    # ------------------------------------------------------------------
    # Cleaning & String Matching Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_text(text: str) -> str:
        text = text.strip().lower()
        # Preserve useful punctuation but collapse whitespace.
        text = re.sub(r"\s+", " ", text)
        return text

    @staticmethod
    def _contains_phrase(text: str, phrase: str) -> bool:
        """Checks if a phrase occurs within the text as a discrete word/phrase match."""
        pattern = r"\b" + re.escape(phrase) + r"\b"
        return bool(re.search(pattern, text, flags=re.IGNORECASE))

    @staticmethod
    def _topic_alias_matches(text: str, alias: str) -> bool:
        """Checks if a topic alias or abbreviation matches in text."""
        # For abbreviations like 'hf', 'af', 'mi', ensure strict boundary matching
        pattern = r"\b" + re.escape(alias) + r"\b"
        if bool(re.search(pattern, text, flags=re.IGNORECASE)):
            # Check context dependencies if necessary
            if alias in CONTEXT_DEPENDENT_ABBREVIATIONS:
                return any(cue in text for cue in MEDICAL_QUERY_CUES)
            return True
        return False

    @staticmethod
    def _unique(items: List[str]) -> List[str]:
        """Preserves order while removing duplicate strings."""
        seen = set()
        res = []
        for item in items:
            if item not in seen:
                seen.add(item)
                res.append(item)
        return res

    # ------------------------------------------------------------------
    # Technical classification
    # ------------------------------------------------------------------

    def _classify_technical_request(
        self,
        text: str,
    ) -> Optional[ScopeResult]:
        matched_terms: List[str] = []

        for term in TECHNICAL_ACTIONS:
            if self._contains_phrase(text, term):
                matched_terms.append(term)

        technical_terms_found = [
            term
            for term in TECHNICAL_TERMS
            if self._contains_phrase(text, term)
        ]

        matched_terms.extend(technical_terms_found)

        technical_domains_found = [
            term
            for term in TECHNICAL_DOMAINS
            if self._contains_phrase(text, term)
        ]

        matched_terms.extend(technical_domains_found)

        if not matched_terms:
            return None

        has_clear_technical_action = any(
            self._contains_phrase(text, action)
            for action in TECHNICAL_ACTIONS
        )

        has_multiple_technical_signals = (
            len(technical_terms_found) + len(technical_domains_found) >= 2
        )

        if has_clear_technical_action or has_multiple_technical_signals:
            return ScopeResult(
                in_scope=False,
                scope="technical_request",
                reason="The query is primarily a software, programming, or technical request.",
                confidence=0.96,
                matched_terms=self._unique(matched_terms),
            )

        return None

    # ------------------------------------------------------------------
    # Explicit topic classification
    # ------------------------------------------------------------------

    def _classify_explicit_topic(
        self,
        text: str,
    ) -> Optional[ScopeResult]:
        matched: List[Tuple[str, str]] = []

        for topic, aliases in self.cardio_topics.items():
            for alias in aliases:
                if self._topic_alias_matches(text, alias):
                    matched.append((topic, alias))

        if not matched:
            return None

        topic_scores: Dict[str, int] = {}

        for topic, alias in matched:
            topic_scores[topic] = topic_scores.get(topic, 0) + len(alias)

        selected_topic = max(
            topic_scores,
            key=topic_scores.get,
        )

        selected_aliases = [
            alias
            for topic, alias in matched
            if topic == selected_topic
        ]

        return ScopeResult(
            in_scope=True,
            scope=selected_topic,
            reason=f"Explicit cardiovascular topic detected: {selected_topic.replace('_', ' ')}.",
            confidence=0.98,
            matched_terms=self._unique(selected_aliases),
        )

    # ------------------------------------------------------------------
    # Cardiovascular symptom classification
    # ------------------------------------------------------------------

    def _classify_cardio_symptom(
        self,
        text: str,
    ) -> Optional[ScopeResult]:
        matched = [
            symptom
            for symptom in self.cardio_symptoms
            if self._contains_phrase(text, symptom)
        ]

        if not matched:
            return None

        return ScopeResult(
            in_scope=True,
            scope="cardiovascular_symptoms",
            reason="A cardiovascular-relevant symptom was detected; the symptom is not treated as a diagnosis.",
            confidence=0.90,
            matched_terms=self._unique(matched),
        )

    # ------------------------------------------------------------------
    # Generic symptom + context classification
    # ------------------------------------------------------------------

    def _classify_contextual_symptom(
        self,
        text: str,
    ) -> Optional[ScopeResult]:
        symptoms = [
            symptom
            for symptom in self.generic_symptoms
            if self._contains_phrase(text, symptom)
        ]

        if not symptoms:
            return None

        cardio_context = [
            term
            for term in self.cardio_context
            if self._contains_phrase(text, term)
        ]

        medical_context = [
            term
            for term in self.medical_context
            if self._contains_phrase(text, term)
        ]

        if cardio_context and medical_context:
            matched = self._unique(symptoms + cardio_context + medical_context)
            return ScopeResult(
                in_scope=True,
                scope="contextual_symptoms",
                reason="Generic symptoms combined with cardiovascular and medical context detected.",
                confidence=0.88,
                matched_terms=matched,
            )

        return None

    # ------------------------------------------------------------------
    # Medical & Cardiovascular context classification
    # ------------------------------------------------------------------

    def _classify_medical_cardio_context(
        self,
        text: str,
    ) -> Optional[ScopeResult]:
        cardio_matches = [
            term
            for term in self.cardio_context
            if self._contains_phrase(text, term)
        ]

        medical_matches = [
            term
            for term in self.medical_context
            if self._contains_phrase(text, term)
        ]

        if cardio_matches and medical_matches:
            matched = self._unique(cardio_matches + medical_matches)
            return ScopeResult(
                in_scope=True,
                scope="medical_cardio_context",
                reason="General cardiovascular and medical terminology present.",
                confidence=0.85,
                matched_terms=matched,
            )

        return None

    # ------------------------------------------------------------------
    # General health context classification
    # ------------------------------------------------------------------

    def _classify_general_health_context(
        self,
        text: str,
    ) -> Optional[ScopeResult]:
        cardio_matches = [
            term
            for term in self.cardio_context
            if self._contains_phrase(text, term)
        ]

        if cardio_matches:
            return ScopeResult(
                in_scope=True,
                scope="general_cardio_health",
                reason="General cardiovascular term detected in query.",
                confidence=0.80,
                matched_terms=self._unique(cardio_matches),
            )

        return None


# ---------------------------------------------------------------------------
# Compatibility aliases / module-level convenience API
# ---------------------------------------------------------------------------

_default_classifier = ScopeClassifier()


def classify_scope(query: str) -> ScopeResult:
    """
    Module-level convenience wrapper.

    Example:
        result = classify_scope("What are the symptoms of CHF?")
    """
    return _default_classifier.classify(query)


def is_in_scope(query: str) -> bool:
    """
    Module-level convenience wrapper returning only the scope decision.
    """
    return _default_classifier.is_in_scope(query)


__all__ = [
    "ScopeResult",
    "ScopeClassifier",
    "classify_scope",
    "is_in_scope",
    "CARDIOVASCULAR_TOPICS",
    "CARDIOVASCULAR_SYMPTOMS",
    "CARDIOVASCULAR_CONTEXT",
    "MEDICAL_CONTEXT",
    "GENERIC_SYMPTOMS",
    "STRONG_MEDICAL_ABBREVIATIONS",
    "CONTEXT_DEPENDENT_ABBREVIATIONS",
]
