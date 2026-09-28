"""
CardioGuide AI - Core Orchestrator

V1 pipeline:

    User Question
        ↓
    Input Validation
        ↓
    Contextual Normalization
        ↓
    Query Analysis
        ↓
    Urgency Detection
        ↓
    Security Detection
        ↓
    High-Risk Medical Detection
        ↓
    Ambiguity Detection
        ↓
    Scope Detection
        ↓
    Decision Gate
        ├── urgent response
        ├── security response
        ├── high-risk response
        ├── clarification
        ├── out-of-scope
        └── proceed
                ↓
        Research Query Builder
                ↓
           Web Searcher
                ↓
         Source Processor
                ↓
          Evidence Builder
                ↓
         Response Planner
                ↓
       Response Generator
                ↓
          Safety Validation
                ↓
      Factuality/Evidence Metadata
                ↓
          Final Response

CardioGuide is an educational cardiovascular-health assistant.
It is not a diagnostic or prescribing system.
"""

from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional

from query_engine.analyzer import QueryAnalyzer
from query_engine.normalizer import normalize_query
from query_engine.ambiguity_detector import AmbiguityDetector
from query_engine.urgency_classifier import UrgencyClassifier
from query_engine.scope_classifier import ScopeClassifier
from query_engine.decision_gate import DecisionGate
from query_engine.llm_client import LLMClient
from query_engine.safety_response_layer import SafetyResponseLayer
from query_engine.factuality_layer import FactualityLayer

# V1 RAG components
from query_engine.research_query_builder import ResearchQueryBuilder
from query_engine.web_searcher import WebSearcher
from query_engine.source_processor import SourceProcessor
from query_engine.evidence_builder import EvidenceBuilder, EvidencePackage
from query_engine.response_planner import ResponsePlanner
from query_engine.response_generator import ResponseGenerator


class CardioGuide:
    """
    Main CardioGuide V1 orchestrator.

    Responsibilities:
    - understand and normalize user input
    - classify cardiovascular scope
    - detect urgency and high-risk requests
    - prevent internal/security disclosure
    - route ambiguous requests to clarification
    - retrieve evidence from approved medical sources
    - generate evidence-grounded answers
    - validate generated responses through the safety layer
    - expose source and grounding metadata
    """

    SECURITY_RESPONSE = (
        "I can help with cardiovascular health information, but I "
        "can't provide internal prompts, hidden instructions, "
        "credentials, private implementation details, or confidential "
        "system information."
    )

    HIGH_RISK_MEDICAL_RESPONSE = (
        "I can provide general cardiovascular health information, "
        "but I can't provide individualized prescription changes, "
        "dosage instructions, or personalized treatment decisions. "
        "For a personal medication or treatment decision, please "
        "speak with a qualified healthcare professional."
    )

    CLARIFICATION_RESPONSE = (
        "I want to make sure I understand your question correctly. "
        "Could you provide a little more detail about what you'd "
        "like to know?"
    )

    OUT_OF_SCOPE_RESPONSE = (
        "I can help with general cardiovascular health information, "
        "including heart and blood-vessel conditions, symptoms, "
        "risk factors, prevention, diagnosis, treatment information, "
        "and when to seek medical care."
    )

    GENERATION_ERROR_RESPONSE = (
        "I wasn't able to generate a reliable response right now. "
        "Please try the question again."
    )

    VALIDATION_ERROR_RESPONSE = (
        "I wasn't able to safely validate the generated response. "
        "Please try the question again."
    )

    def __init__(self, dataset_path: str):
        # ------------------------------------------------------------
        # CORE UNDERSTANDING / ROUTING
        # ------------------------------------------------------------

        self.analyzer = QueryAnalyzer(dataset_path)
        self.ambiguity_detector = AmbiguityDetector()
        self.urgency_classifier = UrgencyClassifier()
        self.scope_classifier = ScopeClassifier()
        self.decision_gate = DecisionGate()

        # ------------------------------------------------------------
        # MODEL / SAFETY
        # ------------------------------------------------------------

        self.llm = LLMClient()
        self.safety_layer = SafetyResponseLayer()
        self.factuality_layer = FactualityLayer()

        # ------------------------------------------------------------
        # V1 RAG / RESEARCH ENGINE
        # ------------------------------------------------------------

        self.research_query_builder = ResearchQueryBuilder()
        self.web_searcher = WebSearcher()
        self.source_processor = SourceProcessor()
        self.evidence_builder = EvidenceBuilder()
        self.response_planner = ResponsePlanner()

        # ResponseGenerator owns the LLM call used for grounded
        # synthesis. Reusing the same configured model family keeps
        # generation behavior consistent.
        self.response_generator = ResponseGenerator(llm=self.llm)

    # ==================================================================
    # PUBLIC API
    # ==================================================================

    def ask(
        self,
        question: str,
        evidence: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Process one user question through the complete CardioGuide V1
        pipeline.

        Parameters
        ----------
        question:
            User's original question.

        evidence:
            Optional externally supplied evidence.

            Supported forms:
            - EvidencePackage
            - list of source dictionaries/processed sources

            When omitted, CardioGuide performs its own V1 research
            pipeline.

        Returns
        -------
        Dict[str, Any]
            Stable CardioGuide response containing:
            - action
            - answer
            - sources
            - safety_note
            - grounded
            - topic
            - intent
            - response_strategy
        """

        pipeline_start = time.time()

        # ------------------------------------------------------------
        # 0. INPUT VALIDATION
        # ------------------------------------------------------------

        if not isinstance(question, str):
            return self._build_response(
                action="clarify",
                answer="Please provide a cardiovascular health question.",
            )

        original_question = question.strip()

        if not original_question:
            return self._build_response(
                action="clarify",
                answer="Please provide a cardiovascular health question.",
            )

        # ------------------------------------------------------------
        # 1. CONTEXTUAL NORMALIZATION
        # ------------------------------------------------------------

        stage_start = time.time()

        try:
            normalized_question = normalize_query(original_question)
        except Exception as exc:
            print("[NORMALIZER] failed:", type(exc).__name__)
            normalized_question = original_question

        if not isinstance(normalized_question, str):
            normalized_question = original_question

        normalized_question = normalized_question.strip()

        if not normalized_question:
            normalized_question = original_question

        print(
            f"[TIMING] normalization: "
            f"{time.time() - stage_start:.2f}s"
        )
        print(f"[NORMALIZED] {normalized_question}")

        # ------------------------------------------------------------
        # 2. QUERY ANALYSIS
        # ------------------------------------------------------------

        stage_start = time.time()

        try:
            analysis = self.analyzer.analyze(
                normalized_question,
                normalized=True,
            )
        except Exception as exc:
            print("[ANALYZER] failed:", type(exc).__name__)
            analysis = None

        print(
            f"[TIMING] analyzer: "
            f"{time.time() - stage_start:.2f}s"
        )

        # ------------------------------------------------------------
        # 3. URGENCY DETECTION
        # ------------------------------------------------------------

        stage_start = time.time()

        try:
            urgency_result = self.urgency_classifier.classify(
                normalized_question
            )
            urgent = bool(
                getattr(urgency_result, "urgent", False)
            )
        except Exception as exc:
            print("[URGENCY] failed:", type(exc).__name__)
            urgency_result = None
            urgent = False

        print(
            f"[TIMING] urgency: "
            f"{time.time() - stage_start:.2f}s"
        )

        # ------------------------------------------------------------
        # 4. SECURITY DETECTION
        # ------------------------------------------------------------

        stage_start = time.time()

        security_sensitive = (
            self._is_security_sensitive(original_question)
            or self._is_security_sensitive(normalized_question)
        )

        print(
            f"[TIMING] security: "
            f"{time.time() - stage_start:.2f}s"
        )

        # ------------------------------------------------------------
        # 5. HIGH-RISK MEDICAL DETECTION
        # ------------------------------------------------------------

        stage_start = time.time()

        high_risk_medical = self._is_high_risk_medical_request(
            normalized_question
        )

        print(
            f"[TIMING] high-risk medical: "
            f"{time.time() - stage_start:.2f}s"
        )

        # ------------------------------------------------------------
        # 6. AMBIGUITY DETECTION
        # ------------------------------------------------------------

        stage_start = time.time()

        try:
            ambiguity_result = self.ambiguity_detector.detect(
                normalized_question
            )
            ambiguous = bool(
                getattr(ambiguity_result, "ambiguous", False)
            )
        except Exception as exc:
            print("[AMBIGUITY] failed:", type(exc).__name__)
            ambiguity_result = None
            ambiguous = False

        print(
            f"[TIMING] ambiguity: "
            f"{time.time() - stage_start:.2f}s"
        )

        # ------------------------------------------------------------
        # 7. SCOPE DETECTION
        # ------------------------------------------------------------

        stage_start = time.time()

        try:
            scope_result = self.scope_classifier.classify(
                normalized_question
            )
            in_scope = bool(
                getattr(scope_result, "in_scope", False)
            )
        except Exception as exc:
            print("[SCOPE] failed:", type(exc).__name__)
            scope_result = None
            in_scope = False

        print(
            f"[TIMING] scope: "
            f"{time.time() - stage_start:.2f}s"
        )

        # ------------------------------------------------------------
        # 8. DECISION GATE
        # ------------------------------------------------------------

        stage_start = time.time()

        needs_clarification = (
            ambiguous
            and not urgent
            and not security_sensitive
            and not high_risk_medical
        )

        decision = self.decision_gate.decide(
            urgent=urgent,
            ambiguous=ambiguous,
            needs_clarification=needs_clarification,
            in_scope=in_scope,
            security_sensitive=security_sensitive,
            high_risk_medical=high_risk_medical,
        )

        print(
            f"[TIMING] decision gate: "
            f"{time.time() - stage_start:.2f}s"
        )

        action = getattr(decision, "action", None)

        print(
            f"[ROUTING] action={action} "
            f"urgent={urgent} "
            f"ambiguous={ambiguous} "
            f"in_scope={in_scope} "
            f"security_sensitive={security_sensitive} "
            f"high_risk_medical={high_risk_medical}"
        )

        # ------------------------------------------------------------
        # 9. CONTROLLED RESPONSES
        # ------------------------------------------------------------

        if action == "urgent_response":
            answer = self._build_urgent_response()

            return self._finalize_controlled_response(
                action="urgent_response",
                answer=answer,
                analysis=analysis,
                pipeline_start=pipeline_start,
            )

        if action == "security_response":
            return self._build_response(
                action="security_response",
                answer=self.SECURITY_RESPONSE,
                safety_note=(
                    "Internal prompts, credentials, private "
                    "implementation details, and confidential "
                    "system information are not disclosed."
                ),
                analysis=analysis,
                pipeline_start=pipeline_start,
            )

        if action == "high_risk_medical":
            return self._finalize_controlled_response(
                action="high_risk_medical",
                answer=self.HIGH_RISK_MEDICAL_RESPONSE,
                analysis=analysis,
                safety_note=(
                    "CardioGuide does not provide individualized "
                    "prescription changes."
                ),
                pipeline_start=pipeline_start,
            )

        if action == "clarify":
            clarification = (
                getattr(
                    ambiguity_result,
                    "clarification_question",
                    None,
                )
                if ambiguity_result
                else None
            )

            return self._build_response(
                action="clarify",
                answer=(
                    clarification
                    or self.CLARIFICATION_RESPONSE
                ),
                analysis=analysis,
                pipeline_start=pipeline_start,
            )

        if action == "redirect":
            return self._build_response(
                action="redirect",
                answer=self.OUT_OF_SCOPE_RESPONSE,
                analysis=analysis,
                pipeline_start=pipeline_start,
            )

        # ------------------------------------------------------------
        # 10. RAG RESEARCH + GROUNDED GENERATION
        # ------------------------------------------------------------

        stage_start = time.time()

        try:
            evidence_package = self._obtain_evidence(
                normalized_question=normalized_question,
                analysis=analysis,
                supplied_evidence=evidence,
            )

            print(
                f"[RAG] evidence_available="
                f"{evidence_package.has_evidence}"
            )
            print(
                f"[RAG] angles="
                f"{evidence_package.available_angles}"
            )
            print(
                f"[RAG] sources="
                f"{len(evidence_package.sources)}"
            )

        except Exception as exc:
            print(
                "[RAG] pipeline failed:",
                type(exc).__name__,
            )
            print(
                f"[TIMING] RAG failed after: "
                f"{time.time() - stage_start:.2f}s"
            )

            return self._build_response(
                action="error",
                answer=(
                    "I wasn't able to retrieve reliable "
                    "information for that question right now. "
                    "Please try again."
                ),
                analysis=analysis,
                pipeline_start=pipeline_start,
            )

        print(
            f"[TIMING] RAG: "
            f"{time.time() - stage_start:.2f}s"
        )

        if not evidence_package.has_evidence:
            print(
                f"[TIMING] TOTAL: "
                f"{time.time() - pipeline_start:.2f}s"
            )

            return self._build_response(
                action="research_unavailable",
                answer=(
                    "I couldn't retrieve enough reliable "
                    "information from the approved medical sources "
                    "to answer that safely right now. "
                    "Please try again shortly."
                ),
                analysis=analysis,
                sources=[],
                grounded=False,
                pipeline_start=pipeline_start,
            )

        # ------------------------------------------------------------
        # 10A. RESPONSE PLAN
        # ------------------------------------------------------------

        stage_start = time.time()

        try:
            response_plan = self.response_planner.plan(
                analysis,
                evidence_package,
            )
        except Exception as exc:
            print(
                "[RESPONSE PLANNER] failed:",
                type(exc).__name__,
            )

            return self._build_response(
                action="error",
                answer=(
                    "I wasn't able to safely plan a response "
                    "from the retrieved information."
                ),
                analysis=analysis,
                pipeline_start=pipeline_start,
            )

        print(
            f"[TIMING] response planning: "
            f"{time.time() - stage_start:.2f}s"
        )

        print(f"[PLAN] {response_plan}")

        # ------------------------------------------------------------
        # 10B. GROUNDED RESPONSE GENERATION
        # ------------------------------------------------------------

        stage_start = time.time()

        try:
            generated = self.response_generator.generate(
                normalized_question,
                evidence_package,
                response_plan,
            )
        except Exception as exc:
            print(
                "[RESPONSE GENERATOR] failed:",
                type(exc).__name__,
            )
            print(
                f"[TIMING] generation failed after: "
                f"{time.time() - stage_start:.2f}s"
            )
            print(
                f"[TIMING] TOTAL: "
                f"{time.time() - pipeline_start:.2f}s"
            )

            return self._build_response(
                action="error",
                answer=self.GENERATION_ERROR_RESPONSE,
                analysis=analysis,
                pipeline_start=pipeline_start,
            )

        print(
            f"[TIMING] grounded generation: "
            f"{time.time() - stage_start:.2f}s"
        )

        answer = (
            generated.get("answer", "")
            if isinstance(generated, dict)
            else ""
        )

        answer = self._clean_text(answer)

        if not answer:
            return self._build_response(
                action="error",
                answer=self.GENERATION_ERROR_RESPONSE,
                analysis=analysis,
                pipeline_start=pipeline_start,
            )

        generated_sources = (
            generated.get("sources", [])
            if isinstance(generated, dict)
            else []
        )

        safety_note = (
            generated.get("safety_note")
            if isinstance(generated, dict)
            else None
        )

        grounded = bool(
            generated.get("grounded", False)
            if isinstance(generated, dict)
            else False
        )

        # ------------------------------------------------------------
        # 11. SAFETY VALIDATION
        # ------------------------------------------------------------

        stage_start = time.time()

        try:
            safety_result = self.safety_layer.validate(
                answer=answer,
                urgent=urgent,
            )

            safe = bool(
                getattr(
                    safety_result,
                    "safe",
                    False,
                )
            )

            final_answer = (
                getattr(
                    safety_result,
                    "answer",
                    None,
                )
                or ""
            ).strip()

        except Exception as exc:
            print(
                "[SAFETY] validation failed:",
                type(exc).__name__,
            )

            return self._build_response(
                action="safety_error",
                answer=self.VALIDATION_ERROR_RESPONSE,
                safety_note="Safety validation failed.",
                analysis=analysis,
                sources=generated_sources,
                grounded=False,
                pipeline_start=pipeline_start,
            )

        print(
            f"[TIMING] safety validation: "
            f"{time.time() - stage_start:.2f}s"
        )

        if not safe or not final_answer:
            return self._build_response(
                action="safety_block",
                answer=(
                    "I couldn't provide that response safely. "
                    "Please rephrase the question or ask about "
                    "general cardiovascular health information."
                ),
                safety_note="Response failed safety validation.",
                analysis=analysis,
                sources=generated_sources,
                grounded=False,
                pipeline_start=pipeline_start,
            )

        # ------------------------------------------------------------
        # 12. FACTUALITY / EVIDENCE METADATA
        # ------------------------------------------------------------

        factuality_sources = generated_sources

        try:
            factuality_result = self.factuality_layer.validate(
                answer=final_answer,
                evidence=evidence_package,
            )

            layer_sources = getattr(
                factuality_result,
                "sources",
                [],
            ) or []

            if layer_sources:
                factuality_sources = layer_sources

        except Exception as exc:
            print(
                "[FACTUALITY] validation failed:",
                type(exc).__name__,
            )

        # Keep generator sources if the factuality layer has not
        # performed actual claim-level verification.

        if not factuality_sources:
            factuality_sources = self._extract_sources(
                evidence_package
            )

        # ------------------------------------------------------------
        # 13. FINAL RESPONSE
        # ------------------------------------------------------------

        total_time = time.time() - pipeline_start

        print(
            f"[TIMING] TOTAL: {total_time:.2f}s"
        )

        return self._build_response(
            action="proceed",
            answer=final_answer,
            sources=factuality_sources,
            safety_note=safety_note,
            grounded=grounded,
            analysis=analysis,
            pipeline_start=pipeline_start,
        )

    # ==================================================================
    # RAG
    # ==================================================================

    def _obtain_evidence(
        self,
        normalized_question: str,
        analysis: Any,
        supplied_evidence: Optional[Any] = None,
    ) -> EvidencePackage:
        """
        Obtain evidence either from supplied evidence or from the V1
        research pipeline.
        """

        # ------------------------------------------------------------
        # Existing EvidencePackage
        # ------------------------------------------------------------

        if isinstance(supplied_evidence, EvidencePackage):
            return supplied_evidence

        # ------------------------------------------------------------
        # Supplied list/dict evidence
        # ------------------------------------------------------------

        if supplied_evidence:
            if isinstance(supplied_evidence, list):
                return self.evidence_builder.build(
                    supplied_evidence
                )

            if isinstance(supplied_evidence, dict):
                return self.evidence_builder.build(
                    [supplied_evidence]
                )

        # ------------------------------------------------------------
        # Require analysis before automatic research
        # ------------------------------------------------------------

        if analysis is None:
            raise RuntimeError(
                "Query analysis is required for research."
            )

        # Ensure the research builder receives the actual normalized
        # question represented by QueryAnalysis.
        try:
            analysis.original_question = normalized_question
        except Exception:
            pass

        # ------------------------------------------------------------
        # RESEARCH QUERY BUILDER
        # ------------------------------------------------------------

        research_plan = self.research_query_builder.build(
            analysis
        )

        queries = getattr(
            research_plan,
            "queries",
            None,
        ) or []

        print(
            f"[RAG] research queries: {len(queries)}"
        )

        for research_query in queries:
            print(
                "[RAG QUERY]",
                f"[{getattr(research_query, 'angle', '')}]",
                getattr(research_query, "query", ""),
            )

        if not queries:
            raise RuntimeError(
                "ResearchQueryBuilder returned no queries."
            )

        # ------------------------------------------------------------
        # WEB SEARCH
        # ------------------------------------------------------------

        raw_results = self.web_searcher.search(
            queries,
            max_sources=3,
        )

        raw_results = raw_results or []

        print(
            f"[RAG] raw results: "
            f"{len(raw_results)}"
        )

        if not raw_results:
            return EvidencePackage()

        # ------------------------------------------------------------
        # SOURCE PROCESSING
        # ------------------------------------------------------------

        processed_sources = self.source_processor.process(
            raw_results
        )

        processed_sources = processed_sources or []

        print(
            f"[RAG] processed sources: "
            f"{len(processed_sources)}"
        )

        if not processed_sources:
            return EvidencePackage()

        # ------------------------------------------------------------
        # EVIDENCE BUILDING
        # ------------------------------------------------------------

        evidence_package = self.evidence_builder.build(
            processed_sources
        )

        if not isinstance(
            evidence_package,
            EvidencePackage,
        ):
            raise RuntimeError(
                "EvidenceBuilder did not return EvidencePackage."
            )

        return evidence_package

    # ==================================================================
    # SECURITY
    # ==================================================================

    @staticmethod
    def _is_security_sensitive(question: str) -> bool:
        """
        Detect attempts to obtain hidden implementation/system
        information.

        This is intentionally deterministic and conservative.
        """

        if not isinstance(question, str):
            return False

        text = question.lower()

        patterns = [
            r"\bsystem prompt\b",
            r"\bsystem message\b",
            r"\bhidden prompt\b",
            r"\binternal prompt\b",
            r"\bdeveloper message\b",
            r"\bdeveloper instructions\b",
            r"\bshow.*prompt\b",
            r"\breveal.*prompt\b",
            r"\bprint.*prompt\b",
            r"\bignore.*instructions\b",
            r"\bignore.*previous\b",
            r"\bdisregard.*instructions\b",
            r"\bhidden instructions\b",
            r"\bsecret instructions\b",
            r"\bapi key\b",
            r"\bapi keys\b",
            r"\bpassword\b",
            r"\bcredentials\b",
            r"\benvironment variables\b",
            r"\bsource code\b",
            r"\bprivate implementation\b",
            r"\binternal architecture\b",
        ]

        return any(
            re.search(pattern, text)
            for pattern in patterns
        )

    # ==================================================================
    # HIGH-RISK MEDICAL REQUESTS
    # ==================================================================

    @staticmethod
    def _is_high_risk_medical_request(
        question: str,
    ) -> bool:
        """
        Detect requests for individualized treatment/prescription
        decisions that CardioGuide V1 should not provide.
        """

        if not isinstance(question, str):
            return False

        text = question.lower()

        medication_terms = [
            "medication",
            "medicine",
            "drug",
            "tablet",
            "pill",
            "dose",
            "dosage",
            "prescription",
            "prescribed",
        ]

        individualized_action_terms = [
            "should i stop",
            "should i start",
            "should i increase",
            "should i decrease",
            "should i change",
            "can i stop",
            "can i start",
            "can i increase",
            "can i decrease",
            "change my dose",
            "increase my dose",
            "decrease my dose",
            "what dose should i take",
            "what medication should i take",
            "which medication should i take",
            "what should i take",
        ]

        has_medication_context = any(
            term in text
            for term in medication_terms
        )

        has_individualized_action = any(
            term in text
            for term in individualized_action_terms
        )

        return (
            has_medication_context
            and has_individualized_action
        )

    # ==================================================================
    # URGENT RESPONSE
    # ==================================================================

    @staticmethod
    def _build_urgent_response() -> str:
        return (
            "If you are experiencing severe or sudden symptoms such "
            "as chest pain or pressure, severe shortness of breath, "
            "fainting, or sudden weakness or numbness, seek emergency "
            "medical care immediately. Do not rely on CardioGuide to "
            "determine whether an emergency is occurring."
        )

    # ==================================================================
    # SOURCE HELPERS
    # ==================================================================

    @staticmethod
    def _extract_sources(
        evidence: EvidencePackage,
    ) -> List[Dict[str, Any]]:
        """
        Convert EvidencePackage sources into the stable source format
        exposed by CardioGuide.
        """

        sources: List[Dict[str, Any]] = []

        for source in getattr(
            evidence,
            "sources",
            [],
        ) or []:

            if isinstance(source, dict):
                title = source.get("title", "")
                url = source.get("url", "")
                domain = source.get("domain", "")
                angle = source.get("angle", "")

            else:
                title = getattr(source, "title", "")
                url = getattr(source, "url", "")
                domain = getattr(source, "domain", "")
                angle = getattr(source, "angle", "")

            if not title and not url:
                continue

            sources.append(
                {
                    "title": title,
                    "url": url,
                    "domain": domain,
                    "angle": angle,
                }
            )

        return sources

    # ==================================================================
    # RESPONSE BUILDING
    # ==================================================================

    def _build_response(
        self,
        action: str,
        answer: str,
        sources: Optional[List[Any]] = None,
        safety_note: Optional[str] = None,
        grounded: bool = False,
        analysis: Any = None,
        pipeline_start: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Build the stable public CardioGuide response contract.
        """

        response: Dict[str, Any] = {
            "action": action,
            "answer": answer,
            "sources": sources or [],
            "safety_note": safety_note,
            "grounded": bool(grounded),
        }

        if analysis is not None:
            response.update(
                {
                    "topic": getattr(
                        analysis,
                        "topic",
                        None,
                    ),
                    "intent": getattr(
                        analysis,
                        "intent",
                        None,
                    ),
                    "response_strategy": getattr(
                        analysis,
                        "response_strategy",
                        None,
                    ),
                }
            )

        if pipeline_start is not None:
            response["processing_time_seconds"] = round(
                time.time() - pipeline_start,
                2,
            )

        return response

    def _finalize_controlled_response(
        self,
        action: str,
        answer: str,
        analysis: Any = None,
        safety_note: Optional[str] = None,
        pipeline_start: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Finalize a deterministic controlled response.

        Controlled responses do not require RAG because they are routing
        and safety behavior rather than generated medical education.
        """

        return self._build_response(
            action=action,
            answer=answer,
            sources=[],
            safety_note=safety_note,
            grounded=False,
            analysis=analysis,
            pipeline_start=pipeline_start,
        )

    # ==================================================================
    # TEXT HELPERS
    # ==================================================================

    @staticmethod
    def _clean_text(value: Any) -> str:
        if not isinstance(value, str):
            return ""

        value = value.strip()

        if not value:
            return ""

        # Remove accidental model wrappers without attempting to rewrite
        # the medical content.
        value = re.sub(
            r"^```(?:text|markdown)?\s*",
            "",
            value,
            flags=re.IGNORECASE,
        )

        value = re.sub(
            r"\s*```$",
            "",
            value,
        )

        return value.strip()