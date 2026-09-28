from dataclasses import dataclass
import re


@dataclass
class UrgencyResult:
    level: str
    urgent: bool
    matched_signals: list[str]


class UrgencyClassifier:
    """
    High-sensitivity emergency symptom classifier.

    This classifier does NOT diagnose a condition.

    It determines whether the wording contains a combination of
    current/personal symptoms that warrants immediate emergency
    routing.

    The design intentionally favors sensitivity for potentially
    dangerous cardiovascular presentations.
    """

    # ============================================================
    # SYMPTOM SIGNALS
    # ============================================================

    CHEST_PATTERNS = [
        r"\bchest pain\b",
        r"\bchest pressure\b",
        r"\bchest tightness\b",
        r"\bchest discomfort\b",
        r"\bchest heaviness\b",
        r"\bheavy chest\b",
        r"\bpressure\b.{0,50}\bchest\b",
        r"\bchest\b.{0,50}\bpressure\b",
        r"\bpressure\b.{0,50}\bbreastbone\b",
        r"\bpressure\b.{0,50}\bmiddle of (?:my|the|his|her)\s+chest\b",
        r"\b(?:pain|pressure|tightness|heaviness)\b.{0,50}\b(?:center|middle)\b.{0,30}\bchest\b",
    ]

    BREATHING_PATTERNS = [
        r"\bshortness of breath\b",
        r"\bshort of breath\b",
        r"\bbreathless\b",
        r"\bdifficulty breathing\b",
        r"\btrouble breathing\b",
        r"\bhard to breathe\b",
        r"\bhaving trouble breathing\b",
        r"\bstruggling to breathe\b",
        r"\bcannot breathe\b",
        r"\bcan't breathe\b",
        r"\bunable to breathe\b",
    ]

    SWEATING_PATTERNS = [
        r"\bsweating\b",
        r"\bsweat(?:ing)? badly\b",
        r"\bbreaking out in a sweat\b",
        r"\bclammy\b",
        r"\bdiaphoresis\b",
        r"\bcold sweat\b",
    ]

    NAUSEA_PATTERNS = [
        r"\bnausea\b",
        r"\bnauseous\b",
        r"\bfeels sick\b",
        r"\bfeeling sick\b",
        r"\bsick to (?:my|his|her|their) stomach\b",
        r"\bvomiting\b",
        r"\bthrowing up\b",
    ]

    RADIATION_PATTERNS = [
        r"\bpain\b.{0,60}\b(?:spreading|radiating|going|moving|extending)\b.{0,40}\b(?:arm|jaw|back|shoulder)\b",
        r"\b(?:spreading|radiating|going|moving|extending)\b.{0,40}\b(?:arm|jaw|back|shoulder)\b",
        r"\bpain\b.{0,40}\b(?:left arm|right arm|both arms)\b",
        r"\bpain\b.{0,40}\b(?:jaw|back|shoulder)\b",
        r"\b(?:pain|pressure|discomfort)\b.{0,50}\b(?:into|toward|towards)\b.{0,30}\b(?:arm|jaw|back|shoulder)\b",
    ]

    STROKE_PATTERNS = [
        r"\bface drooping\b",
        r"\bfacial drooping\b",
        r"\bface is drooping\b",
        r"\bslurred speech\b",
        r"\bspeech is slurred\b",
        r"\bdifficulty speaking\b",
        r"\bcannot speak\b",
        r"\bcan't speak\b",
        r"\bsudden weakness\b",
        r"\bsudden numbness\b",
        r"\bweakness on one side\b",
        r"\bnumbness on one side\b",
        r"\bweakness in one side\b",
        r"\bnumbness in one side\b",
        r"\bsudden confusion\b",
        r"\bsudden vision loss\b",
        r"\bvision suddenly\b",
        r"\btrouble understanding speech\b",
    ]

    SYNCOPE_PATTERNS = [
        r"\bfainted\b",
        r"\bfainting\b",
        r"\bpassed out\b",
        r"\blost consciousness\b",
        r"\bloss of consciousness\b",
        r"\babout to pass out\b",
        r"\bfeel like i(?:'m| am) going to pass out\b",
    ]

    SEVERE_BREATHING_PATTERNS = [
        r"\bsevere shortness of breath\b",
        r"\bstruggling to breathe\b",
        r"\bcannot breathe\b",
        r"\bcan't breathe\b",
        r"\bunable to breathe\b",
    ]

    # ============================================================
    # CURRENT / PERSONAL CONTEXT
    # ============================================================

    CURRENT_CONTEXT_PATTERNS = [
        r"\bright now\b",
        r"\bcurrently\b",
        r"\bat the moment\b",
        r"\btoday\b",
        r"\bjust now\b",
        r"\bjust started\b",
        r"\bsuddenly\b",
        r"\bsudden\b",

        r"\bi am\b",
        r"\bi'm\b",
        r"\bi have\b",
        r"\bi am having\b",
        r"\bi'm having\b",
        r"\bi feel\b",
        r"\bi am feeling\b",
        r"\bi'm feeling\b",
        r"\bmy\b",

        r"\bhe is\b",
        r"\bhe's\b",
        r"\bhis\b",
        r"\bshe is\b",
        r"\bshe's\b",
        r"\bher\b",

        r"\bdad\b",
        r"\bfather\b",
        r"\bmom\b",
        r"\bmother\b",
        r"\bparent\b",

        r"\bis having\b",
        r"\bare having\b",
        r"\bhas\b",
        r"\bfeels\b",
        r"\bfeeling\b",
        r"\bexperiencing\b",
    ]

    EDUCATIONAL_CONTEXT_PATTERNS = [
        r"\bwhat are\b",
        r"\bwhat is\b",
        r"\bwhat are the symptoms\b",
        r"\bcommon symptoms\b",
        r"\bsigns of\b",
        r"\bsymptoms of\b",
        r"\brisk factors\b",
        r"\bhow does\b",
        r"\bcan you explain\b",
        r"\bexplain\b",
        r"\bdefinition\b",
    ]

    # ============================================================
    # PUBLIC CLASSIFICATION
    # ============================================================

    def classify(self, question: str) -> UrgencyResult:
        if not isinstance(question, str):
            raise TypeError("Question must be a string.")

        text = question.lower().strip()

        if not text:
            return self._normal()

        signals = []

        has_chest = self._matches_any(
            text,
            self.CHEST_PATTERNS,
        )

        has_breathing = self._matches_any(
            text,
            self.BREATHING_PATTERNS,
        )

        has_sweating = self._matches_any(
            text,
            self.SWEATING_PATTERNS,
        )

        has_nausea = self._matches_any(
            text,
            self.NAUSEA_PATTERNS,
        )

        has_radiation = self._matches_any(
            text,
            self.RADIATION_PATTERNS,
        )

        has_stroke = self._matches_any(
            text,
            self.STROKE_PATTERNS,
        )

        has_syncope = self._matches_any(
            text,
            self.SYNCOPE_PATTERNS,
        )

        has_severe_breathing = self._matches_any(
            text,
            self.SEVERE_BREATHING_PATTERNS,
        )

        current_context = self._has_current_context(text)

        # --------------------------------------------------------
        # Record detected signals.
        # --------------------------------------------------------

        if has_chest:
            signals.append("chest_pain")

        if has_breathing:
            signals.append("breathing")

        if has_sweating:
            signals.append("sweating")

        if has_nausea:
            signals.append("nausea")

        if has_radiation:
            signals.append("radiation")

        if has_stroke:
            signals.append("stroke_signs")

        if has_syncope:
            signals.append("fainting")

        # --------------------------------------------------------
        # Stroke warning signs + current context.
        # --------------------------------------------------------

        if has_stroke and current_context:
            return UrgencyResult(
                level="urgent",
                urgent=True,
                matched_signals=signals,
            )

        # --------------------------------------------------------
        # Syncope + current context.
        # --------------------------------------------------------

        if has_syncope and current_context:
            return UrgencyResult(
                level="urgent",
                urgent=True,
                matched_signals=signals,
            )

        # --------------------------------------------------------
        # Severe breathing difficulty + current context.
        # --------------------------------------------------------

        if has_severe_breathing and current_context:
            return UrgencyResult(
                level="urgent",
                urgent=True,
                matched_signals=signals,
            )

        # --------------------------------------------------------
        # Chest symptom combinations.
        #
        # Chest symptom + breathing
        # Chest symptom + sweating
        # Chest symptom + nausea
        # Chest symptom + radiation
        #
        # are treated as potentially emergent when the symptoms
        # are being described as current/personal.
        # --------------------------------------------------------

        if has_chest and current_context:
            associated_red_flags = (
                has_breathing
                or has_sweating
                or has_nausea
                or has_radiation
            )

            if associated_red_flags:
                return UrgencyResult(
                    level="urgent",
                    urgent=True,
                    matched_signals=signals,
                )

            # Current chest pain/pressure itself can warrant
            # urgent routing when the wording clearly indicates
            # a present symptom.
            return UrgencyResult(
                level="urgent",
                urgent=True,
                matched_signals=signals,
            )

        return self._normal()

    # ============================================================
    # HELPERS
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

    def _has_current_context(self, text: str) -> bool:

        if self._matches_any(
            text,
            self.CURRENT_CONTEXT_PATTERNS,
        ):
            return True

        # If there is an explicit current-time phrase, this
        # should strongly indicate a present situation.
        if re.search(
            r"\b(?:right now|currently|today|suddenly|just started)\b",
            text,
            flags=re.IGNORECASE,
        ):
            return True

        return False

    @staticmethod
    def _normal() -> UrgencyResult:
        return UrgencyResult(
            level="normal",
            urgent=False,
            matched_signals=[],
        )