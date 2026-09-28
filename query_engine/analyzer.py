from typing import Dict, List, Optional
import re

import pandas as pd

from query_engine.normalizer import normalize_query
from query_engine.schemas import QueryAnalysis
from query_engine.clinical_terminology import (
    MEDICAL_ALIASES,
    TOPIC_ALIASES,
    normalize_for_analysis,
    contains_phrase,
)


class QueryAnalyzer:
    """
    Cardiovascular query understanding and routing metadata.

    Responsibilities:
        - classify cardiovascular topic
        - detect one or more user intents
        - select the primary intent
        - infer requested depth
        - infer knowledge level
        - infer user goal
        - build response strategy

    The analyzer does NOT:
        - generate medical answers
        - diagnose
        - determine emergency status
        - rewrite the user's query
        - call an LLM for dataset initialization

    Medical terminology is expanded only in the internal
    analysis representation. The user's normalized query
    remains unchanged.
    """

    INTENT_KEYWORDS: Dict[str, List[str]] = {

        # -----------------------------------------------------
        # DEFINITION
        # -----------------------------------------------------

        "definition": [
            "what is",
            "what are",
            "define",
            "definition",
            "meaning of",
            "what does it mean",
            "what does that mean",
            "what does this mean",
            "what does",
            "what do",
            "what exactly is",
            "what exactly are",
            "explain",
            "tell me about",
            "understand what",
            "i dont understand what",
            "i don't understand what",
            "dont understand what",
            "don't understand what",
            "dont get what",
            "don't get what",
            "get what",
        ],

        # -----------------------------------------------------
        # SYMPTOMS
        # -----------------------------------------------------

        "symptoms": [
            "symptom",
            "symptoms",
            "sign",
            "signs",
            "feel",
            "feeling",
            "how does it feel",
            "what does it feel like",
            "what might someone feel",
            "what would i feel",
            "what would someone feel",
        ],

        # -----------------------------------------------------
        # RISK FACTORS
        # -----------------------------------------------------

        "risk_factors": [
            "risk factor",
            "risk factors",
            "risk",
            "at risk",
            "increase my risk",
            "higher risk",
            "contribute to its development",
            "contribute to development",
            "what increases the risk",
            "what raises the risk",
            "what makes me more likely",
        ],

        # -----------------------------------------------------
        # CAUSES
        # -----------------------------------------------------

        "causes": [
            "cause",
            "causes",
            "caused by",
            "why does",
            "why do",
            "what leads to",
            "what makes",
            "what causes it",
            "how does it develop",
            "how does it happen",
            "why does this happen",
        ],

        # -----------------------------------------------------
        # DIAGNOSIS
        # -----------------------------------------------------

        "diagnosis": [
            "diagnos",
            "diagnosis",
            "diagnosed",
            "test",
            "tests",
            "testing",
            "how do doctors",
            "how is it detected",
            "detect",
            "detected",
            "confirm a diagnosis",
            "confirm the diagnosis",
            "rule out",
            "ruling out",
        ],

        # -----------------------------------------------------
        # COMPLICATIONS
        # -----------------------------------------------------

        "complications": [
            "complication",
            "complications",
            "damage",
            "problems can it cause",
            "what can it cause",
            "what problems can",
            "long term effects",
            "long-term effects",
            "consequences",
            "life-threatening",
            "serious",
            "how serious",
            "is this serious",
            "is it serious",
            "can it be dangerous",
            "dangerous",
        ],

        # -----------------------------------------------------
        # PREVENTION
        # -----------------------------------------------------

        "prevention": [
            "prevent",
            "prevention",
            "prevented",
            "avoid",
            "lower my risk",
            "reduce my risk",
            "how can it be prevented",
            "lifestyle change",
            "lifestyle changes",
            "healthy lifestyle",
            "healthy habits",
            "protect my heart",
            "protect the heart",
            "change my lifestyle",
            "diet and exercise",
            "exercise and diet",
        ],

        # -----------------------------------------------------
        # TREATMENT / MANAGEMENT
        # -----------------------------------------------------

        "treatment": [
            "treat",
            "treatment",
            "treated",
            "manage",
            "management",
            "managed",
            "control",
            "controlled",
            "how can it be managed",
            "how is it treated",
            "medication",
            "medications",
            "medicine",
            "medicines",
            "meds",
            "drug",
            "drugs",
            "pill",
            "pills",
            "taking my medication",
            "take my medication",
            "forget my medication",
            "forget my meds",
            "miss my medication",
            "missed my medication",
            "miss my meds",
            "missed my meds",
            "medication adherence",
            "adherence",
            "compliance",
            "surgery",
            "surgical",
            "intervention",
        ],

        # -----------------------------------------------------
        # MONITORING
        # -----------------------------------------------------

        "monitoring": [
            "monitor",
            "monitoring",
            "how often",
            "how frequently",
            "check",
            "checking",
            "measure",
            "measurement",
            "measured",
            "blood pressure readings",
            "how often should",
            "home monitoring",
            "monitor at home",
            "check at home",
            "measure at home",
            "home blood pressure",
        ],

        # -----------------------------------------------------
        # COMPARISON
        # -----------------------------------------------------

        "comparison": [
            "difference between",
            "different from",
            "compare",
            "comparison",
            "versus",
            " vs ",
            "vs.",
            "distinguish",
            "distinguishing",
            "how does it differ",
            "how do they differ",
        ],

        # -----------------------------------------------------
        # SIDE EFFECTS
        # -----------------------------------------------------

        "side_effects": [
            "side effect",
            "side effects",
            "adverse effect",
            "adverse effects",
            "reaction to medication",
            "reaction to medicine",
            "reaction to meds",
        ],

        # -----------------------------------------------------
        # WHEN TO SEEK MEDICAL CARE
        # -----------------------------------------------------

        "when_to_seek_medical_care": [
            "when should i seek medical care",
            "when should someone seek medical care",
            "when should i see a doctor",
            "when should someone see a doctor",
            "when is it an emergency",
            "when is this an emergency",
            "emergency",
            "urgent medical care",
            "urgent care",
            "seek medical attention",
            "seek medical help",
            "when to seek medical care",
            "when should i worry",
            "when should someone worry",
        ],
    }

    INTENT_PRIORITY = [
        "when_to_seek_medical_care",
        "diagnosis",
        "treatment",
        "prevention",
        "monitoring",
        "complications",
        "symptoms",
        "risk_factors",
        "causes",
        "comparison",
        "side_effects",
        "definition",
    ]

    MEDICAL_ALIASES = MEDICAL_ALIASES
    TOPIC_ALIASES = TOPIC_ALIASES

    def __init__(self, csv_path: str):
        self.queries = pd.read_csv(csv_path)

        if "question" not in self.queries.columns:
            raise ValueError(
                "Query dataset must contain a 'question' column."
            )

        self._dataset_question_lookup = (
            self._build_dataset_question_lookup()
        )

        self._known_topics = self._build_known_topics()

    # ============================================================
    # PUBLIC API
    # ============================================================

    def analyze(
        self,
        question: str,
        normalized: bool = False,
    ) -> QueryAnalysis:

        if not isinstance(question, str):
            raise TypeError("Question must be a string.")

        if normalized:
            normalized_question = question.strip()
        else:
            normalized_question = normalize_query(question)

        if not normalized_question:
            normalized_question = question.strip()

        match_key = self._canonicalize_for_match(
            normalized_question
        )

        row = self._dataset_question_lookup.get(match_key)

        if row is not None:

            dataset_topic = str(
                row.get("topic", "") or ""
            ).strip()

            dataset_intent = str(
                row.get("intent", "") or ""
            ).strip()

            detected_intents = self._detect_intents(
                normalized_question
            )

            if detected_intents:
                primary_intent = self._select_primary_intent(
                    detected_intents
                )
            else:
                primary_intent = dataset_intent

            if not primary_intent:
                primary_intent = "general_information"

            strategy = self._build_response_strategy(
                detected_intents=detected_intents,
                explicit_depth=str(
                    row.get("explicit_depth", "") or ""
                ),
            )

            return QueryAnalysis(
                original_question=question,
                topic=dataset_topic,
                subtopic=str(
                    row.get("subtopic", "") or ""
                ),
                intent=primary_intent,
                explicit_depth=str(
                    row.get("explicit_depth", "") or ""
                ),
                knowledge_level=str(
                    row.get("knowledge_level", "") or ""
                ),
                user_goal=str(
                    row.get("user_goal", "") or ""
                ),
                response_strategy=strategy,
                visual_support=str(
                    row.get("visual_support", "") or "recommended"
                ),
            )

        topic = self._detect_topic(
            normalized_question
        )

        detected_intents = self._detect_intents(
            normalized_question
        )

        if detected_intents:
            intent = self._select_primary_intent(
                detected_intents
            )
        else:
            intent = "general_information"

        explicit_depth = self._detect_depth(
            normalized_question
        )

        knowledge_level = self._detect_knowledge_level(
            normalized_question
        )

        user_goal = self._detect_user_goal(
            normalized_question,
            detected_intents,
        )

        response_strategy = self._build_response_strategy(
            detected_intents=detected_intents,
            explicit_depth=explicit_depth,
        )

        return QueryAnalysis(
            original_question=question,
            topic=topic or "",
            subtopic="",
            intent=intent,
            explicit_depth=explicit_depth,
            knowledge_level=knowledge_level,
            user_goal=user_goal,
            response_strategy=response_strategy,
            visual_support="recommended",
        )

    def get_detected_intents(
        self,
        question: str,
        normalized: bool = False,
    ) -> List[str]:

        if not isinstance(question, str):
            raise TypeError("Question must be a string.")

        if normalized:
            normalized_question = question.strip()
        else:
            normalized_question = normalize_query(question)

        return self._detect_intents(
            normalized_question
        )

    # ============================================================
    # ANALYSIS REPRESENTATION
    # ============================================================

    def _build_analysis_text(
        self,
        question: str,
    ) -> str:
        return normalize_for_analysis(
            question
        )

    # ============================================================
    # DATASET
    # ============================================================

    def _build_dataset_question_lookup(
        self,
    ) -> Dict[str, dict]:

        lookup: Dict[str, dict] = {}

        for _, row in self.queries.iterrows():

            question = str(
                row.get("question", "") or ""
            ).strip()

            if not question:
                continue

            key = self._canonicalize_for_match(
                question
            )

            if not key:
                continue

            if key not in lookup:
                lookup[key] = row.to_dict()

        return lookup

    def _canonicalize_for_match(
        self,
        text: str,
    ) -> str:

        if not isinstance(text, str):
            return ""

        text = text.strip().lower()

        if not text:
            return ""

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        text = re.sub(
            r"^[^\w]+|[^\w]+$",
            "",
            text,
        )

        text = re.sub(
            r"[!?.,;:]+",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        return text

    def _build_known_topics(
        self,
    ) -> List[str]:

        topics = set()

        if "topic" in self.queries.columns:

            for value in self.queries["topic"].dropna():

                value = str(value).strip().lower()

                if value:
                    topics.add(value)

        return sorted(
            topics,
            key=len,
            reverse=True,
        )

    # ============================================================
    # TOPIC
    # ============================================================

    def _detect_topic(
        self,
        question: str,
    ) -> Optional[str]:

        analysis_text = self._build_analysis_text(
            question
        )

        aliases = sorted(
            self.TOPIC_ALIASES.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        )

        for phrase, topic in aliases:

            if self._contains_phrase(
                analysis_text,
                phrase,
            ):
                return topic

        for topic in self._known_topics:

            if self._contains_phrase(
                analysis_text,
                topic,
            ):
                return topic

        return None

    # ============================================================
    # INTENTS
    # ============================================================

    def _detect_intents(
        self,
        question: str,
    ) -> List[str]:

        analysis_text = self._build_analysis_text(
            question
        )

        detected: List[str] = []

        for intent, keywords in self.INTENT_KEYWORDS.items():

            for keyword in keywords:

                if self._contains_keyword(
                    analysis_text,
                    keyword,
                ):
                    detected.append(intent)
                    break

        # --------------------------------------------------------
        # Semantic patterns that are difficult to represent as
        # simple keyword matches.
        # --------------------------------------------------------

        # "what X means"
        if re.search(
            r"\bwhat\s+(?:does|do)\b.+\bmean\b",
            analysis_text,
            flags=re.IGNORECASE,
        ):
            if "definition" not in detected:
                detected.append("definition")

        # "I don't understand/get what X means"
        if re.search(
            r"\b(?:dont|don't)\s+(?:really\s+)?"
            r"(?:understand|get)\s+what\b",
            analysis_text,
            flags=re.IGNORECASE,
        ):
            if "definition" not in detected:
                detected.append("definition")

        # Medication adherence / forgetting medication.
        if re.search(
            r"\b(?:forget|forgot|forgetting|miss|missed|"
            r"missing|skip|skipped)\b.+\b"
            r"(?:meds?|medication|medicine|pills?)\b",
            analysis_text,
            flags=re.IGNORECASE,
        ):
            if "treatment" not in detected:
                detected.append("treatment")

        # Lifestyle changes used to control/manage a condition.
        if re.search(
            r"\b(?:lifestyle|diet|exercise|physical activity)\b"
            r".*\b(?:change|changes|help|fix|manage|control|lower|reduce)\b",
            analysis_text,
            flags=re.IGNORECASE,
        ):
            if "prevention" not in detected:
                detected.append("prevention")

        # "Can X fix/manage/control it?"
        if re.search(
            r"\b(?:can|could)\b.+\b"
            r"(?:fix|manage|control|improve|lower|reduce)\b",
            analysis_text,
            flags=re.IGNORECASE,
        ):
            if "treatment" not in detected:
                detected.append("treatment")

        # "Is this serious?"
        if re.search(
            r"\b(?:is|how)\b.+\b(?:serious|dangerous)\b",
            analysis_text,
            flags=re.IGNORECASE,
        ):
            if "complications" not in detected:
                detected.append("complications")

        # Generic educational fallback.
        if (
            not detected
            and (
                analysis_text.startswith("what ")
                or analysis_text.startswith("explain ")
                or analysis_text.startswith("tell me about ")
            )
        ):
            detected.append("definition")

        return detected

    def _select_primary_intent(
        self,
        intents: List[str],
    ) -> str:

        if not intents:
            return "general_information"

        for priority_intent in self.INTENT_PRIORITY:

            if priority_intent in intents:
                return priority_intent

        return intents[0]

    # ============================================================
    # RESPONSE STRATEGY
    # ============================================================

    def _build_response_strategy(
        self,
        detected_intents: List[str],
        explicit_depth: str,
    ) -> str:

        if not detected_intents:

            if explicit_depth == "simple":
                return "simple educational explanation"

            return "clear educational explanation"

        if len(detected_intents) == 1:

            if explicit_depth == "simple":
                return (
                    "simple educational explanation; "
                    f"angle={detected_intents[0]}"
                )

            return (
                "focused educational explanation; "
                f"angle={detected_intents[0]}"
            )

        ordered = [
            intent
            for intent in self.INTENT_PRIORITY
            if intent in detected_intents
        ]

        return (
            "structured multi-angle educational explanation; "
            f"angles={','.join(ordered)}"
        )

    # ============================================================
    # DEPTH
    # ============================================================

    def _detect_depth(
        self,
        question: str,
    ) -> str:

        question = self._build_analysis_text(
            question
        )

        simple_markers = [
            "simply",
            "simple",
            "easy",
            "beginner",
            "not a medical person",
            "non medical",
            "non-medical",
            "layman",
            "in simple terms",
            "explain it simply",
        ]

        detailed_markers = [
            "detailed",
            "deep",
            "in depth",
            "in-depth",
            "comprehensive",
            "thorough",
            "everything",
            "all i need to know",
        ]

        if any(
            marker in question
            for marker in simple_markers
        ):
            return "simple"

        if any(
            marker in question
            for marker in detailed_markers
        ):
            return "detailed"

        return "standard"

    # ============================================================
    # KNOWLEDGE LEVEL
    # ============================================================

    def _detect_knowledge_level(
        self,
        question: str,
    ) -> str:

        question = self._build_analysis_text(
            question
        )

        if any(
            marker in question
            for marker in [
                "not a medical person",
                "non medical",
                "non-medical",
                "beginner",
                "simple terms",
                "layman",
            ]
        ):
            return "beginner"

        if any(
            marker in question
            for marker in [
                "pathophysiology",
                "mechanism",
                "clinical",
                "medical terminology",
                "physiology",
            ]
        ):
            return "advanced"

        return "general"

    # ============================================================
    # USER GOAL
    # ============================================================

    def _detect_user_goal(
        self,
        question: str,
        detected_intents: Optional[List[str]] = None,
    ) -> str:

        intents = detected_intents or []

        if "when_to_seek_medical_care" in intents:
            return "understanding when to seek medical care"

        if "treatment" in intents:
            return "management"

        if "prevention" in intents:
            return "prevention"

        if "diagnosis" in intents:
            return "understanding diagnosis"

        if "monitoring" in intents:
            return "monitoring"

        if "comparison" in intents:
            return "comparison"

        if "symptoms" in intents:
            return "understanding symptoms"

        if "risk_factors" in intents:
            return "understanding risk factors"

        if "causes" in intents:
            return "understanding causes"

        if "complications" in intents:
            return "understanding complications"

        if "side_effects" in intents:
            return "understanding medication side effects"

        if "definition" in intents:
            return "understanding the condition"

        return "education"

    # ============================================================
    # MATCHING
    # ============================================================

    @staticmethod
    def _contains_phrase(
        text: str,
        phrase: str,
    ) -> bool:

        return contains_phrase(
            text,
            phrase,
        )

    @staticmethod
    def _contains_keyword(
        text: str,
        keyword: str,
    ) -> bool:

        text = text.strip().lower()
        keyword = keyword.strip().lower()

        if not text or not keyword:
            return False

        if " " in keyword:
            return keyword in text

        return bool(
            re.search(
                rf"\b{re.escape(keyword)}\w*\b",
                text,
            )
        )