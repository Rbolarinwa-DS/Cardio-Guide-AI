from dataclasses import dataclass
from typing import Dict, List

from query_engine.source_processor import ProcessedSource


@dataclass
class EvidencePackage:
    question: str
    combined_evidence: str
    evidence_by_angle: Dict[str, str]
    sources: List[dict]


class EvidenceBuilder:

    ANGLES = [
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

    def build(
        self,
        question: str,
        sources: List[ProcessedSource],
    ) -> EvidencePackage:

        evidence_by_angle = {
            angle: []
            for angle in self.ANGLES
        }

        source_metadata = []

        for source in sources:

            content = source.content.strip()

            if not content:
                continue

            angle = source.angle

            if angle not in evidence_by_angle:
                continue

            evidence_by_angle[angle].append(
                f"[{source.domain}]\n{content}"
            )

            source_metadata.append(
                {
                    "title": source.title,
                    "url": source.url,
                    "domain": source.domain,
                    "angle": source.angle,
                    "query": source.query,
                }
            )

        # Remove duplicate source metadata.
        unique_sources = {}

        for source in source_metadata:

            key = (
                source["url"],
                source["angle"],
            )

            if key not in unique_sources:
                unique_sources[key] = source

        source_metadata = list(
            unique_sources.values()
        )

        # Convert angle lists into strings.
        formatted_evidence = {}

        for angle, blocks in evidence_by_angle.items():

            if blocks:
                formatted_evidence[angle] = (
                    "\n\n".join(blocks)
                )
            else:
                formatted_evidence[angle] = (
                    "No evidence retrieved."
                )

        # Build combined evidence.
        combined_blocks = []

        for angle in self.ANGLES:

            evidence = formatted_evidence[angle]

            if evidence == "No evidence retrieved.":
                continue

            combined_blocks.append(
                f"--- {angle.upper()} ---\n"
                f"{evidence}"
            )

        if combined_blocks:

            combined_evidence = "\n\n".join(
                combined_blocks
            )

        else:

            combined_evidence = (
                "No reliable evidence was retrieved "
                "from the approved medical sources."
            )

        return EvidencePackage(
            question=question,
            combined_evidence=combined_evidence,
            evidence_by_angle=formatted_evidence,
            sources=source_metadata,
        )