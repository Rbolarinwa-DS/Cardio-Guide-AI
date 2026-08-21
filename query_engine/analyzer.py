import pandas as pd

from query_engine.normalizer import normalize_query
from query_engine.schemas import QueryAnalysis


class QueryAnalyzer:

    def __init__(self, csv_path: str):
        self.queries = pd.read_csv(csv_path)

    def analyze(self, question: str) -> QueryAnalysis:
        normalized_question = normalize_query(question)

        # Exact normalized-question match
        normalized_dataset_questions = (
            self.queries["question"]
            .astype(str)
            .apply(normalize_query)
        )

        matches = self.queries[
            normalized_dataset_questions == normalized_question
        ]

        if not matches.empty:
            row = matches.iloc[0]

            return QueryAnalysis(
                original_question=question,
                topic=row["topic"],
                subtopic=row["subtopic"],
                intent=row["intent"],
                explicit_depth=row["explicit_depth"],
                knowledge_level=row["knowledge_level"],
                user_goal=row["user_goal"],
                response_strategy=row["response_strategy"],
                visual_support=row["visual_support"],
            )

        # No exact match yet
        return QueryAnalysis(
            original_question=question
        )