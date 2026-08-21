from query_engine.analyzer import QueryAnalyzer
from query_engine.research_query_builder import ResearchQueryBuilder
from query_engine.web_searcher import WebSearcher
from query_engine.source_processor import SourceProcessor
from query_engine.evidence_builder import EvidenceBuilder
from query_engine.response_planner import ResponsePlanner
from query_engine.response_generator import ResponseGenerator

from query_engine.ambiguity_detector import AmbiguityDetector
from query_engine.urgency_classifier import UrgencyClassifier
from query_engine.scope_classifier import ScopeClassifier
from query_engine.decision_gate import DecisionGate


class CardioGuide:

    def __init__(self, csv_path: str):

        # --------------------------------
        # Core research pipeline
        # --------------------------------

        self.analyzer = QueryAnalyzer(csv_path)

        self.query_builder = ResearchQueryBuilder()

        self.web_searcher = WebSearcher()

        self.source_processor = SourceProcessor()

        self.evidence_builder = EvidenceBuilder()

        self.response_planner = ResponsePlanner()

        self.response_generator = ResponseGenerator()

        # --------------------------------
        # Safety / understanding pipeline
        # --------------------------------

        self.ambiguity_detector = AmbiguityDetector()

        self.urgency_classifier = UrgencyClassifier()

        self.scope_classifier = ScopeClassifier()

        self.decision_gate = DecisionGate()

    # ==================================================
    # ASK
    # ==================================================

    def ask(self, question: str):

        # --------------------------------
        # Basic input validation
        # --------------------------------

        if not isinstance(question, str):

            return {
                "action": "clarify",
                "message": (
                    "Please provide your cardiovascular "
                    "health question."
                ),
            }

        question = question.strip()

        if not question:

            return {
                "action": "clarify",
                "message": (
                    "Please provide a cardiovascular "
                    "health question."
                ),
            }

        # --------------------------------
        # 1. Analyze question
        # --------------------------------

        analysis = self.analyzer.analyze(
            question
        )

        # --------------------------------
        # 2. Safety / understanding checks
        # --------------------------------

        urgency = (
            self.urgency_classifier.classify(
                question
            )
        )

        ambiguity = (
            self.ambiguity_detector.detect(
                question
            )
        )

        scope = (
            self.scope_classifier.classify(
                question
            )
        )

        # --------------------------------
        # 3. Decision gate
        # --------------------------------

        decision = self.decision_gate.decide(
            urgent=urgency.urgent,
            ambiguous=ambiguity.ambiguous,
            needs_clarification=False,
            in_scope=scope.in_scope,
        )

        # --------------------------------
        # 4. Handle non-research paths
        # --------------------------------

        if decision.action == "urgent_response":

            return {
                "action": "urgent_response",
                "message": (
                    "Your message may describe symptoms "
                    "that could require urgent medical "
                    "attention. Please seek immediate "
                    "medical care."
                ),
            }

        if decision.action == "clarify":

            return {
                "action": "clarify",
                "message": (
                    ambiguity.clarification_question
                ),
            }

        if decision.action == "redirect":

            return {
                "action": "redirect",
                "message": (
                    "CardioGuide focuses on cardiovascular "
                    "health education and cannot reliably "
                    "answer questions outside that scope."
                ),
            }

        # --------------------------------
        # 5. Build multi-angle research plan
        # --------------------------------

        plan = self.query_builder.build(
            analysis
        )

        # --------------------------------
        # 6. Search approved sources
        # --------------------------------

        search_results = (
            self.web_searcher.search(
                plan.queries
            )
        )

        # --------------------------------
        # 7. Process retrieved sources
        # --------------------------------

        processed_sources = (
            self.source_processor.process(
                search_results
            )
        )

        # --------------------------------
        # 8. Build structured evidence
        # --------------------------------

        evidence = (
            self.evidence_builder.build(
                question=question,
                sources=processed_sources,
            )
        )

        # --------------------------------
        # 9. Plan response
        # --------------------------------

        response_plan = (
            self.response_planner.plan(
                analysis,
                evidence,
            )
        )

        # --------------------------------
        # 10. Generate response
        # --------------------------------

        response = (
            self.response_generator.generate(
                evidence,
                response_plan,
            )
        )

        # --------------------------------
        # 11. Final result
        # --------------------------------

        return {
    "action": "proceed",
    "response": response["answer"],
    "answer": response["answer"],
    "evidence": evidence,
    "flashcards": response["flashcards"],
    "visual_support": response["visual_support"],
    "sources": response["sources"],
    "safety_note": response["safety_note"],
}