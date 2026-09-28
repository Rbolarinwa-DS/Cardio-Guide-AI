from dataclasses import dataclass
from typing import Dict, List

from query_engine.schemas import QueryAnalysis


@dataclass
class ResearchQuery:
    angle: str
    query: str


@dataclass
class ResearchPlan:
    queries: List[ResearchQuery]


class ResearchQueryBuilder:
    """
    Converts QueryAnalysis into focused research queries.

    The builder separates the actual medical subject from generic
    concepts such as "lifestyle", "prevention", or "risk factors".

    Example:
        User asks:
        "What increases the risk of heart disease and what lifestyle
        habits help protect the heart?"

        Analyzer may identify:
            topic = "lifestyle"
            intent = "risk_factors"

        The builder must NOT produce:
            "What are the risk factors for lifestyle?"

        Instead it resolves the actual subject:
            "heart disease"

        and produces focused cardiovascular queries.
    """

    RESEARCH_ANGLES = [
        "definition",
        "symptoms",
        "causes",
        "risk factors",
        "diagnosis",
        "complications",
        "prevention",
        "management and treatment",
        "types",
        "monitoring",
        "lifestyle",
        "when to seek medical care",
    ]

    INTENT_ANGLES: Dict[str, List[str]] = {
        "definition": [
            "definition",
            "types",
        ],
        "symptoms": [
            "symptoms",
            "when to seek medical care",
        ],
        "causes": [
            "causes",
            "risk factors",
        ],
        "risk_factors": [
            "risk factors",
            "causes",
            "prevention",
        ],
        "diagnosis": [
            "diagnosis",
            "monitoring",
        ],
        "complications": [
            "complications",
            "when to seek medical care",
        ],
        "prevention": [
            "prevention",
            "risk factors",
            "lifestyle",
        ],
        "treatment": [
            "management and treatment",
            "lifestyle",
            "monitoring",
        ],
        "side_effects": [
            "management and treatment",
            "monitoring",
        ],
        "monitoring": [
            "monitoring",
            "diagnosis",
        ],
        "comparison": [
            "definition",
            "types",
        ],
        "general_information": [
            "definition",
            "symptoms",
            "causes",
            "risk factors",
            "diagnosis",
            "complications",
            "prevention",
            "management and treatment",
            "monitoring",
            "lifestyle",
            "when to seek medical care",
        ],
    }

    # Generic concepts that are NOT themselves suitable medical topics.
    GENERIC_TOPICS = {
        "lifestyle",
        "prevention",
        "risk factors",
        "risk factor",
        "causes",
        "symptoms",
        "diagnosis",
        "treatment",
        "management",
        "monitoring",
        "health",
        "medical health",
        "general health",
        "cardiovascular health",
    }

    # ============================================================
    # MAIN BUILD
    # ============================================================

    def build(
        self,
        analysis: QueryAnalysis,
    ) -> ResearchPlan:

        topic = self._resolve_topic(analysis)

        intent = self._normalize_intent(
            getattr(analysis, "intent", None)
        )

        angles = self.INTENT_ANGLES.get(
            intent,
            self.INTENT_ANGLES["general_information"],
        )

        # Remove duplicates while preserving order.
        selected_angles = []

        for angle in angles:
            if angle not in selected_angles:
                selected_angles.append(angle)

        queries = [
            ResearchQuery(
                angle=angle,
                query=self._build_query(
                    topic,
                    angle,
                ),
            )
            for angle in selected_angles
        ]

        return ResearchPlan(
            queries=queries
        )

    # ============================================================
    # QUERY GENERATION
    # ============================================================

    def _build_query(
        self,
        topic: str,
        angle: str,
    ) -> str:

        templates = {
            "definition": (
                f"What is {topic}?"
            ),
            "symptoms": (
                f"What are the symptoms and signs of {topic}?"
            ),
            "causes": (
                f"What causes {topic}?"
            ),
            "risk factors": (
                f"What are the risk factors for {topic}?"
            ),
            "diagnosis": (
                f"How is {topic} diagnosed?"
            ),
            "complications": (
                f"What complications can {topic} cause?"
            ),
            "prevention": (
                f"How can {topic} be prevented?"
            ),
            "management and treatment": (
                f"How is {topic} managed and treated?"
            ),
            "types": (
                f"What are the types of {topic}?"
            ),
            "monitoring": (
                f"How should {topic} be monitored?"
            ),
            "lifestyle": (
                f"What lifestyle factors affect {topic}?"
            ),
            "when to seek medical care": (
                f"When should someone seek medical care "
                f"for {topic}?"
            ),
        }

        return templates.get(
            angle,
            f"Medical information about {topic}.",
        )

    # ============================================================
    # INTENT NORMALIZATION
    # ============================================================

    def _normalize_intent(
        self,
        intent,
    ) -> str:

        if not intent:
            return "general_information"

        normalized = str(
            intent
        ).strip().lower()

        aliases = {
            "risk factors": "risk_factors",
            "risk factor": "risk_factors",
            "risk-factor": "risk_factors",

            "general": "general_information",
            "overview": "general_information",
            "general information": "general_information",

            "manage": "treatment",
            "management": "treatment",

            "side effect": "side_effects",
            "side-effects": "side_effects",
            "side effects": "side_effects",
        }

        return aliases.get(
            normalized,
            normalized,
        )

    # ============================================================
    # TOPIC RESOLUTION
    # ============================================================

    def _resolve_topic(
        self,
        analysis: QueryAnalysis,
    ) -> str:
        """
        Resolve the actual medical subject.

        Important:
        The analyzer can sometimes identify a generic concept such as
        "lifestyle" as the topic even though the user's actual subject
        is "heart disease".

        In that situation, inspect the original question for a concrete
        cardiovascular subject before falling back to the analyzer topic.
        """

        topic = self._get_analysis_topic(analysis)

        if topic and not self._is_generic_topic(topic):
            return topic

        question = self._get_original_question(analysis)

        if question:
            cardiovascular_topic = (
                self._extract_cardiovascular_topic(question)
            )

            if cardiovascular_topic:
                return cardiovascular_topic

        if topic:
            return topic

        return "cardiovascular health"

    # ============================================================
    # ANALYSIS TOPIC
    # ============================================================

    def _get_analysis_topic(
        self,
        analysis: QueryAnalysis,
    ) -> str | None:

        attributes = (
            "topic",
            "condition",
            "subject",
            "medical_topic",
        )

        for attribute in attributes:

            value = getattr(
                analysis,
                attribute,
                None,
            )

            if value:
                value = str(value).strip()

                if value:
                    return value

        return None

    # ============================================================
    # ORIGINAL QUESTION
    # ============================================================

    def _get_original_question(
        self,
        analysis: QueryAnalysis,
    ) -> str | None:

        attributes = (
            "original_question",
            "question",
        )

        for attribute in attributes:

            value = getattr(
                analysis,
                attribute,
                None,
            )

            if value:
                value = str(value).strip()

                if value:
                    return value

        return None

    # ============================================================
    # GENERIC TOPIC DETECTION
    # ============================================================

    def _is_generic_topic(
        self,
        topic: str,
    ) -> bool:

        normalized = (
            topic
            .strip()
            .lower()
        )

        return normalized in self.GENERIC_TOPICS

    # ============================================================
    # CARDIOVASCULAR SUBJECT EXTRACTION
    # ============================================================

    def _extract_cardiovascular_topic(
        self,
        question: str,
    ) -> str | None:
        """
        Recover a concrete cardiovascular subject from the user's
        original question when the analyzer selected a generic topic.

        This is intentionally conservative. It only returns subjects
        that are explicitly present in the question.
        """

        normalized = (
            question
            .strip()
            .lower()
        )

        cardiovascular_topics = [
            (
                "heart disease",
                "heart disease",
            ),
            (
                "cardiovascular disease",
                "cardiovascular disease",
            ),
            (
                "heart failure",
                "heart failure",
            ),
            (
                "heart attack",
                "heart attack",
            ),
            (
                "coronary artery disease",
                "coronary artery disease",
            ),
            (
                "high blood pressure",
                "high blood pressure",
            ),
            (
                "hypertension",
                "hypertension",
            ),
            (
                "high cholesterol",
                "high cholesterol",
            ),
            (
                "cholesterol",
                "cholesterol",
            ),
            (
                "stroke",
                "stroke",
            ),
            (
                "atrial fibrillation",
                "atrial fibrillation",
            ),
            (
                "afib",
                "atrial fibrillation",
            ),
            (
                "arrhythmia",
                "arrhythmia",
            ),
            (
                "atherosclerosis",
                "atherosclerosis",
            ),
            (
                "rheumatic heart disease",
                "rheumatic heart disease",
            ),
        ]

        for phrase, canonical_name in cardiovascular_topics:
            if phrase in normalized:
                return canonical_name

        return None