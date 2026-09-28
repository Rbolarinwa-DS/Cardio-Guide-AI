from dataclasses import dataclass
import re


@dataclass
class SafetyResult:
    answer: str
    safe: bool
    modified: bool
    violations: list[str]


class SafetyResponseLayer:
    """
    Final safety and privacy validation layer for CardioGuide AI.

    This layer does NOT determine whether medical claims are
    factually correct.

    Factuality and evidence grounding belong to FactualityLayer.

    Responsibilities:
        1. Prevent diagnostic certainty.
        2. Prevent dangerous medical delays.
        3. Prevent unsafe medication instructions.
        4. Prevent unsafe emergency instructions.
        5. Prevent internal/private information disclosure.
        6. Detect malformed model output.
        7. Enforce minimum emergency guidance.
    """

    # ============================================================
    # INTERNAL / PRIVATE INFORMATION
    # ============================================================

    INTERNAL_PATTERNS = [
        r"\bsystem prompt\b",
        r"\bsystem message\b",
        r"\bdeveloper message\b",
        r"\bdeveloper instructions\b",
        r"\bdeveloper prompt\b",
        r"\bhidden prompt\b",
        r"\binternal prompt\b",
        r"\bchain[- ]of[- ]thought\b",
        r"\binternal reasoning\b",
        r"\bprivate system\b",
        r"\bapi key\b",
        r"\bsecret key\b",
        r"\benvironment variable\b",
        r"\benv variable\b",
        r"\bollama\b",
        r"\bqwen3\b",
        r"\bqwen\b",
        r"\bmodel parameters\b",
        r"\bretrieval pipeline\b",
        r"\binternal architecture\b",
        r"\bprivate implementation\b",
        r"\bhidden instructions\b",
        r"\bprivate configuration\b",
        r"\bconfidential configuration\b",
    ]

    # ============================================================
    # DIAGNOSTIC CERTAINTY
    # ============================================================

    DIAGNOSIS_PATTERNS = [
        r"\byou definitely have\b",
        r"\byou certainly have\b",
        r"\byou are suffering from\b",
        r"\bthis confirms\b",
        r"\bthis means you have\b",
        r"\byour symptoms prove\b",
        r"\bthe diagnosis is\b",
        r"\byou have been diagnosed with\b",
        r"\bthis is definitely\b",
        r"\bthis is certainly\b",
        r"\bthere is no doubt that you have\b",
        r"\byou clearly have\b",
    ]

    # ============================================================
    # DANGEROUS DELAY
    # ============================================================

    DELAY_PATTERNS = [
        r"\bwait and see\b",
        r"\bwait until tomorrow\b",
        r"\bwait a few days\b",
        r"\bwait several days\b",
        r"\bwait for it to pass\b",
        r"\bwait for the symptoms to pass\b",
        r"\bno need to seek medical care\b",
        r"\bno need for medical care\b",
        r"\bno need to see a doctor\b",
        r"\bdo not seek medical care\b",
        r"\bdon't seek medical care\b",
        r"\bignore (?:the )?symptoms\b",
        r"\bignore these symptoms\b",
        r"\bit is safe to ignore\b",
    ]

    # ============================================================
    # UNSAFE MEDICATION INSTRUCTIONS
    # ============================================================

    MEDICATION_PATTERNS = [
        r"\bstop taking\b",
        r"\bstop your medication\b",
        r"\bstop the medication\b",
        r"\bdouble (?:your )?dose\b",
        r"\bdouble the dose\b",
        r"\bincrease (?:your )?dose\b",
        r"\bdecrease (?:your )?dose\b",
        r"\bchange your medication\b",
        r"\bswitch your medication\b",
        r"\bstart taking\b",
        r"\bchange the dose\b",
        r"\badjust your dose\b",
        r"\badjust the dose\b",
        r"\btake another dose\b",
        r"\bskip your dose\b",
        r"\bskip the dose\b",

        # Direct dosage instruction.
        r"\b(?:take|use)\s+\d+(?:\.\d+)?\s*(?:mg|mcg|g|milligrams|micrograms)\b",

        # Explicit user-directed medication decisions.
        r"\byou should\s+(?:take|stop|start|increase|decrease|double|halve|change|switch)\b",
        r"\byou can\s+(?:take|stop|start|increase|decrease|double|halve|change|switch)\b",
    ]

    # ============================================================
    # UNSAFE EMERGENCY ACTIONS
    # ============================================================

    UNSAFE_EMERGENCY_PATTERNS = [
        r"\byou should\s+take a shower\b",
        r"\byou should\s+exercise\b",
        r"\byou should\s+continue exercising\b",
        r"\byou should\s+continue walking\b",
        r"\byou should\s+ignore the symptoms\b",
        r"\byou should\s+drive yourself\b",
        r"\byou can\s+drive yourself\b",
        r"\byou should\s+wait for it to pass\b",
        r"\byou should\s+wait for the symptoms to pass\b",
    ]

    # ============================================================
    # EMERGENCY GUIDANCE
    # ============================================================

    EMERGENCY_ACTION_PATTERNS = [
        r"\bemergency\b",
        r"\burgent\b",
        r"\bimmediate medical attention\b",
        r"\bseek immediate medical attention\b",
        r"\bseek emergency medical care\b",
        r"\bcontact emergency medical services\b",
        r"\bcontact your local emergency service\b",
        r"\bcall emergency services\b",
        r"\bcall your local emergency number\b",
        r"\bget emergency help\b",
        r"\bseek emergency help\b",
    ]

    # ============================================================
    # MALFORMED OUTPUT
    # ============================================================

    MALFORMED_OUTPUT_PATTERNS = [
        r"<think>",
        r"</think>",
        r"<\|.*?\|>",
        r"\bassistant:\s*$",
        r"\bsystem:\s*$",
        r"\buser:\s*$",
    ]

    # ============================================================
    # CONTROLLED RESPONSES
    # ============================================================

    EMERGENCY_RESPONSE = (
        "The symptoms described may indicate a medical emergency. "
        "Please seek immediate medical attention or contact your "
        "local emergency medical service now. Follow the emergency "
        "service's instructions and avoid driving yourself if you "
        "may be experiencing a medical emergency."
    )

    DIAGNOSTIC_RESPONSE = (
        "These symptoms or findings can be associated with several "
        "conditions, and CardioGuide cannot diagnose an individual. "
        "A qualified healthcare professional should evaluate the "
        "situation."
    )

    INTERNAL_INFORMATION_RESPONSE = (
        "I can provide cardiovascular health information, but I "
        "cannot provide internal system instructions, hidden "
        "prompts, private implementation details, or other "
        "confidential system information."
    )

    MEDICATION_RESPONSE = (
        "Medication decisions such as starting, stopping, changing, "
        "or adjusting a medicine should be made with guidance from "
        "a qualified healthcare professional. CardioGuide can "
        "provide general information about a medication, but it "
        "should not determine an individual's dose or treatment plan."
    )

    DELAY_RESPONSE = (
        "The symptoms described should not be ignored. If they are "
        "severe, sudden, worsening, or otherwise concerning, seek "
        "prompt medical attention rather than waiting for them to "
        "resolve on their own."
    )

    INVALID_RESPONSE = (
        "I’m sorry, but I couldn't produce a reliable response. "
        "Please try the question again."
    )

    # ============================================================
    # PUBLIC VALIDATION
    # ============================================================

    def validate(
        self,
        answer: str,
        urgent: bool = False,
    ) -> SafetyResult:

        if not isinstance(answer, str):
            if urgent:
                return SafetyResult(
                    answer=self.EMERGENCY_RESPONSE,
                    safe=False,
                    modified=True,
                    violations=["invalid_response"],
                )

            return SafetyResult(
                answer=self.INVALID_RESPONSE,
                safe=False,
                modified=True,
                violations=["invalid_response"],
            )

        answer = answer.strip()

        if not answer:
            if urgent:
                return SafetyResult(
                    answer=self.EMERGENCY_RESPONSE,
                    safe=False,
                    modified=True,
                    violations=["empty_response"],
                )

            return SafetyResult(
                answer=self.INVALID_RESPONSE,
                safe=False,
                modified=True,
                violations=["empty_response"],
            )

        violations = self._detect_violations(answer)

        if urgent:
            return self._validate_urgent_response(
                answer=answer,
                violations=violations,
            )

        if not violations:
            return SafetyResult(
                answer=answer,
                safe=True,
                modified=False,
                violations=[],
            )

        repaired = self._repair_response(
            answer=answer,
            violations=violations,
        )

        return SafetyResult(
            answer=repaired,
            safe=False,
            modified=True,
            violations=violations,
        )

    # ============================================================
    # VIOLATION DETECTION
    # ============================================================

    def _detect_violations(
        self,
        answer: str,
    ) -> list[str]:

        violations = []

        if self._matches_any(
            answer,
            self.INTERNAL_PATTERNS,
        ):
            violations.append(
                "internal_information"
            )

        if self._matches_any(
            answer,
            self.DIAGNOSIS_PATTERNS,
        ):
            violations.append(
                "diagnostic_certainty"
            )

        if self._matches_any(
            answer,
            self.DELAY_PATTERNS,
        ):
            violations.append(
                "dangerous_delay"
            )

        if self._matches_any(
            answer,
            self.MEDICATION_PATTERNS,
        ):
            violations.append(
                "medication_instruction"
            )

        if self._matches_any(
            answer,
            self.UNSAFE_EMERGENCY_PATTERNS,
        ):
            violations.append(
                "unsafe_emergency_instruction"
            )

        if self._matches_any(
            answer,
            self.MALFORMED_OUTPUT_PATTERNS,
        ):
            violations.append(
                "malformed_output"
            )

        return violations

    # ============================================================
    # PATTERN MATCHING
    # ============================================================

    @staticmethod
    def _matches_any(
        text: str,
        patterns: list[str],
    ) -> bool:

        return any(
            re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
            for pattern in patterns
        )

    # ============================================================
    # URGENT RESPONSE VALIDATION
    # ============================================================

    def _validate_urgent_response(
        self,
        answer: str,
        violations: list[str],
    ) -> SafetyResult:

        critical_violations = {
            "internal_information",
            "unsafe_emergency_instruction",
            "dangerous_delay",
            "malformed_output",
            "diagnostic_certainty",
        }

        if critical_violations & set(violations):
            return SafetyResult(
                answer=self.EMERGENCY_RESPONSE,
                safe=False,
                modified=True,
                violations=violations,
            )

        has_emergency_language = self._matches_any(
            answer,
            self.EMERGENCY_ACTION_PATTERNS,
        )

        if not has_emergency_language:
            return SafetyResult(
                answer=self.EMERGENCY_RESPONSE,
                safe=False,
                modified=True,
                violations=(
                    violations
                    + ["missing_emergency_guidance"]
                ),
            )

        return SafetyResult(
            answer=answer,
            safe=True,
            modified=False,
            violations=violations,
        )

    # ============================================================
    # RESPONSE REPAIR
    # ============================================================

    def _repair_response(
        self,
        answer: str,
        violations: list[str],
    ) -> str:

        if "internal_information" in violations:
            return self.INTERNAL_INFORMATION_RESPONSE

        if "malformed_output" in violations:
            return self.INVALID_RESPONSE

        if "unsafe_emergency_instruction" in violations:
            return self.EMERGENCY_RESPONSE

        if "dangerous_delay" in violations:
            return self.DELAY_RESPONSE

        if "medication_instruction" in violations:
            return self.MEDICATION_RESPONSE

        if "diagnostic_certainty" in violations:
            return self.DIAGNOSTIC_RESPONSE

        return answer