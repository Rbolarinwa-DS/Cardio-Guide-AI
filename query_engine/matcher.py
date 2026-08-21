from difflib import SequenceMatcher

import pandas as pd

from query_engine.normalizer import normalize_query


class QueryMatcher:

    def __init__(self, csv_path: str, threshold: float = 0.65):
        self.queries = pd.read_csv(csv_path)
        self.threshold = threshold

        self.normalized_questions = (
            self.queries["question"]
            .astype(str)
            .apply(normalize_query)
        )

    def match(self, question: str):
        normalized_question = normalize_query(question)

        best_index = None
        best_score = 0.0

        for index, dataset_question in enumerate(
            self.normalized_questions
        ):
            score = SequenceMatcher(
                None,
                normalized_question,
                dataset_question
            ).ratio()

            if score > best_score:
                best_score = score
                best_index = index

        if best_index is None or best_score < self.threshold:
            return None

        row = self.queries.iloc[best_index]

        return {
            "query_id": row["query_id"],
            "matched_question": row["question"],
            "similarity": round(best_score, 4),
            "topic": row["topic"],
            "subtopic": row["subtopic"],
            "intent": row["intent"],
            "explicit_depth": row["explicit_depth"],
            "knowledge_level": row["knowledge_level"],
            "user_goal": row["user_goal"],
            "response_strategy": row["response_strategy"],
            "visual_support": row["visual_support"],
        }