from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class MeasurementResult:
    measurement_type: str
    values: dict
    unit: Optional[str]
    valid: bool


class MeasurementParser:

    def parse(self, text: str) -> list[MeasurementResult]:
        results = []

        results.extend(self._parse_blood_pressure(text))
        results.extend(self._parse_cholesterol(text))

        return results

    def _parse_blood_pressure(
        self,
        text: str
    ) -> list[MeasurementResult]:

        matches = re.findall(
            r"\b(\d{2,3})\s*/\s*(\d{2,3})\b",
            text
        )

        results = []

        for systolic, diastolic in matches:

            results.append(
                MeasurementResult(
                    measurement_type="blood_pressure",
                    values={
                        "systolic": int(systolic),
                        "diastolic": int(diastolic),
                    },
                    unit="mmHg",
                    valid=True,
                )
            )

        return results

    def _parse_cholesterol(
        self,
        text: str
    ) -> list[MeasurementResult]:

        results = []

        patterns = {
            "LDL": r"\bLDL\s*[:=]?\s*(\d+(?:\.\d+)?)",
            "HDL": r"\bHDL\s*[:=]?\s*(\d+(?:\.\d+)?)",
            "total_cholesterol": (
                r"\b(?:total cholesterol|cholesterol)"
                r"\s*[:=]?\s*(\d+(?:\.\d+)?)"
            ),
        }

        for measurement_type, pattern in patterns.items():

            matches = re.findall(
                pattern,
                text,
                flags=re.IGNORECASE
            )

            for value in matches:

                results.append(
                    MeasurementResult(
                        measurement_type=measurement_type.lower(),
                        values={
                            "value": float(value)
                        },
                        unit="mg/dL",
                        valid=True,
                    )
                )

        return results