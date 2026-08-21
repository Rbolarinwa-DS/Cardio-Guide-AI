import re


def normalize_query(question: str) -> str:
    """
    Normalize a user's question before query analysis.

    This does NOT determine the medical meaning of the question.
    It only cleans the text.
    """

    if not isinstance(question, str):
        raise TypeError("Question must be a string.")

    # Remove leading/trailing whitespace
    question = question.strip()

    # Normalize repeated whitespace
    question = re.sub(r"\s+", " ", question)

    # Normalize apostrophes
    question = question.replace("’", "'")

    # Normalize common informal contractions
    replacements = {
        "what's": "what is",
        "whats": "what is",
        "what're": "what are",
        "how's": "how is",
        "hows": "how is",
        "can't": "cannot",
        "dont": "do not",
        "don't": "do not",
        "isnt": "is not",
        "isn't": "is not",
        "doesnt": "does not",
        "doesn't": "does not",
        "im": "i am",
        "i'm": "i am",
    }

    lower_question = question.lower()

    for old, new in replacements.items():
        lower_question = re.sub(
            rf"\b{re.escape(old)}\b",
            new,
            lower_question
        )

    # Normalize excessive punctuation
    lower_question = re.sub(r"[!?]{2,}", "?", lower_question)

    return lower_question.strip()