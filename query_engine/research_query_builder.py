from dataclasses import dataclass
from typing import List

from query_engine.schemas import QueryAnalysis


@dataclass
class ResearchQuery:
    angle: str
    query: str


@dataclass
class ResearchPlan:
    queries: List[ResearchQuery]


class ResearchQueryBuilder:

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

    def build(self, analysis: QueryAnalysis) -> ResearchPlan:

        topic = self._resolve_topic(analysis)

        queries = [
            ResearchQuery(
                angle="definition",
                query=f"What is {topic}?",
            ),
            ResearchQuery(
                angle="symptoms",
                query=f"What are the symptoms of {topic}?",
            ),
            ResearchQuery(
                angle="causes",
                query=f"What causes {topic}?",
            ),
            ResearchQuery(
                angle="risk factors",
                query=f"What are the risk factors for {topic}?",
            ),
            ResearchQuery(
                angle="diagnosis",
                query=f"How is {topic} diagnosed?",
            ),
            ResearchQuery(
                angle="complications",
                query=f"What complications can {topic} cause?",
            ),
            ResearchQuery(
                angle="prevention",
                query=f"How can {topic} be prevented?",
            ),
            ResearchQuery(
                angle="management and treatment",
                query=f"How is {topic} managed and treated?",
            ),
            ResearchQuery(
                angle="types",
                query=f"What are the different types of {topic}?",
            ),
            ResearchQuery(
                angle="monitoring",
                query=f"How should {topic} be monitored?",
            ),
            ResearchQuery(
                angle="lifestyle",
                query=f"What lifestyle factors are related to {topic}?",
            ),
            ResearchQuery(
                angle="when to seek medical care",
                query=(
                    f"When should someone seek medical care "
                    f"for {topic}?"
                ),
            ),
        ]

        return ResearchPlan(queries=queries)

    def _resolve_topic(self, analysis: QueryAnalysis) -> str:

        for attribute in (
            "topic",
            "condition",
            "subject",
            "medical_topic",
        ):
            value = getattr(analysis, attribute, None)

            if value:
                return str(value).strip()

        question = getattr(analysis, "question", None)

        if question:
            return str(question).strip()

        return "cardiovascular health"