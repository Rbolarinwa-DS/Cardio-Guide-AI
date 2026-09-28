"""
Shared clinical terminology and contextual cardiovascular language handling.

This module is used by routing components such as QueryAnalyzer and
ScopeClassifier.

IMPORTANT:
    - This is NOT a diagnostic engine.
    - It does NOT determine disease from symptoms.
    - It does NOT rewrite the user's actual query.
    - It only creates an internal representation for language/routing.
"""

import re
from typing import Dict


# ---------------------------------------------------------------------
# Shared medical abbreviations / terminology
# ---------------------------------------------------------------------

MEDICAL_ALIASES: Dict[str, str] = {
    # Heart failure
    "congestive heart failure": "heart failure",
    "chf": "heart failure",
    "hf": "heart failure",

    # Breathing
    "shortness of breath": "shortness of breath",
    "sob": "shortness of breath",
    "dyspnea": "shortness of breath",
    "doe": "shortness of breath",

    # Hypertension / blood pressure
    "high blood pressure": "hypertension",
    "high bp": "hypertension",
    "htn": "hypertension",

    # Atrial fibrillation
    "atrial fibrillation": "atrial fibrillation",
    "afib": "atrial fibrillation",
    "a-fib": "atrial fibrillation",

    # "AF" is intentionally treated as a cardiovascular alias.
    # The shared representation is only used internally for routing.
    "af": "atrial fibrillation",

    # Heart attack
    "myocardial infarction": "heart attack",
    "m.i.": "heart attack",
    "mi": "heart attack",

    # Coronary artery disease
    "coronary artery disease": "coronary artery disease",
    "coronary heart disease": "coronary artery disease",
    "cad": "coronary artery disease",

    # Rheumatic heart disease
    "rheumatic heart disease": "rheumatic heart disease",
    "rhd": "rheumatic heart disease",
}


# ---------------------------------------------------------------------
# Topic aliases
# ---------------------------------------------------------------------

TOPIC_ALIASES: Dict[str, str] = {
    "hypertension": "hypertension",
    "high blood pressure": "hypertension",
    "high bp": "hypertension",
    "blood pressure": "hypertension",
    "hypertensive": "hypertension",
    "htn": "hypertension",

    "cholesterol": "cholesterol",
    "high cholesterol": "cholesterol",

    "coronary artery disease": "coronary artery disease",
    "coronary heart disease": "coronary artery disease",
    "coronary disease": "coronary artery disease",
    "cad": "coronary artery disease",

    "heart failure": "heart failure",
    "congestive heart failure": "heart failure",
    "chf": "heart failure",
    "hf": "heart failure",

    "heart attack": "heart attack",
    "myocardial infarction": "heart attack",
    "mi": "heart attack",
    "m.i.": "heart attack",

    "stroke": "stroke",

    "atrial fibrillation": "atrial fibrillation",
    "afib": "atrial fibrillation",
    "a-fib": "atrial fibrillation",
    "a fib": "atrial fibrillation",
    "af": "atrial fibrillation",

    "arrhythmia": "arrhythmia",
    "arrhythmias": "arrhythmia",

    "atherosclerosis": "atherosclerosis",

    "rheumatic heart disease": "rheumatic heart disease",
    "rhd": "rheumatic heart disease",
}


# ---------------------------------------------------------------------
# Symptom terminology
# ---------------------------------------------------------------------

SYMPTOM_ALIASES: Dict[str, str] = {
    "sob": "shortness of breath",
    "dyspnea": "shortness of breath",
    "doe": "shortness of breath",

    "palpitation": "palpitations",
    "palpitations": "palpitations",

    "fast heartbeat": "rapid heartbeat",
    "racing heartbeat": "rapid heartbeat",
    "rapid heartbeat": "rapid heartbeat",

    "irregular heartbeat": "irregular heartbeat",
    "irregular heart beat": "irregular heartbeat",
    "irregular heart rhythm": "irregular heartbeat",
}


# ---------------------------------------------------------------------
# Text normalization for internal analysis only
# ---------------------------------------------------------------------

def normalize_for_analysis(text: str) -> str:
    """
    Create an internal terminology-aware representation.

    This MUST NOT be used as the user's displayed query.

    The function only expands known clinical terminology and abbreviations.
    It does not infer diagnoses from symptoms.
    """
    if not isinstance(text, str):
        return ""

    text = text.strip().lower()

    if not text:
        return ""

    # Normalize common punctuation around M.I.
    text = re.sub(
        r"(?<!\w)m\.i\.(?!\w)",
        " mi ",
        text,
    )

    # Normalize whitespace.
    text = re.sub(r"\s+", " ", text).strip()

    # Longest aliases first.
    aliases = sorted(
        MEDICAL_ALIASES.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )

    for alias, expansion in aliases:
        pattern = rf"(?<!\w){re.escape(alias)}(?!\w)"

        text = re.sub(
            pattern,
            expansion,
            text,
            flags=re.IGNORECASE,
        )

    text = re.sub(r"\s+", " ", text).strip()

    return text


def contains_phrase(text: str, phrase: str) -> bool:
    """
    Boundary-aware phrase matching.
    """
    if not isinstance(text, str) or not isinstance(phrase, str):
        return False

    text = text.strip().lower()
    phrase = phrase.strip().lower()

    if not text or not phrase:
        return False

    return bool(
        re.search(
            rf"(?<!\w){re.escape(phrase)}(?!\w)",
            text,
            flags=re.IGNORECASE,
        )
    )


def contains_any(text: str, phrases) -> bool:
    return any(
        contains_phrase(text, phrase)
        for phrase in phrases
    )


def contains_pattern(text: str, patterns) -> bool:
    if not isinstance(text, str):
        return False

    return any(
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )
        for pattern in patterns
    )


def detect_topic_from_terminology(text: str):
    """
    Return an explicitly expressed cardiovascular topic.

    This function only identifies explicit terminology.
    It does NOT infer a disease from symptoms.
    """
    analysis_text = normalize_for_analysis(text)

    aliases = sorted(
        TOPIC_ALIASES.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )

    for phrase, topic in aliases:
        if contains_phrase(analysis_text, phrase):
            return topic

    return None