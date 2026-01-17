#!/usr/bin/env python3

from pathlib import Path
from typing import Any
import json

from code_wcag_a11y.globals import PROCESSED_DIR, RAW_DIR

from .types.chunk_types import (
    SuccessCriterionChunk,
    TermChunk,
    WcagVersion,
)
from .types.wcag_types import (
    Guideline,
    Principle,
    Successcriterion,
    Term,
    WCAGData,
)
from .utils.keyword_search import find_related_requirements
from .utils.formatter import (
    clean_wcag_text,
    get_base_data,
    get_parent_data,
    extract_techniques_summary,
    extract_testing_requirements,
)


def get_wcag_data(wcag_version: WcagVersion = "2.2") -> WCAGData:
    """Load and parse WCAG JSON data."""

    file_path = RAW_DIR / f"wcag-{ wcag_version}.json"
    print(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return WCAGData.model_validate(data)


def make_success_criteria_chunk(
    success_criteria: Successcriterion,
    guideline: Guideline,
    principle: Principle,
    wcag_version: WcagVersion,
    wcag_data: WCAGData,
) -> SuccessCriterionChunk:
    description = clean_wcag_text(success_criteria.content)

    return {
        **get_base_data(success_criteria, "success_criterion", wcag_version),
        # Content
        "description": description,
        # Hierarchy
        **get_parent_data("guideline", guideline),
        "principle_id": principle.id,
        "principle_num": principle.num,
        "principle_title": principle.title,
        "versions_applicable": success_criteria.versions,
        "techniques": extract_techniques_summary(success_criteria.techniques),
        # Compliance / testing
        "compliance_level": success_criteria.level,
        "testing_requirements": extract_testing_requirements(success_criteria),
        "related_requirements": find_related_requirements(success_criteria, wcag_data),
        # Metadata
        "full_context": f"WCAG {version} Success Criterion {success_criteria.num} ({success_criteria.level}): {success_criteria.title}",
    }


def make_principle_chunk(principle: Principle, version: str) -> PrincipleChunk:
    description = clean_wcag_text(principle.content)
    guideline_ids = [guideline.id for guideline in principle.guidelines]

    guidelines_count = len(principle.guidelines)
    return {
        **get_base_data(principle, "principle", version),
        # Content
        "description": description,
        # Guidelines data under this principle
        "guidelines_count": guidelines_count,
        "guideline_ids": guideline_ids,
        # Metadata
        "full_context": f"WCAG {version} Principle {principle.num}: {principle.title}",
    }


def make_guideline_chunk(guideline: Guideline, principle: Principle, version: str):
    description = clean_wcag_text(guideline.content)
    success_criteria_ids = [
        successcriteria.id for successcriteria in guideline.successcriteria
    ]
    success_criteria_count = len(guideline.successcriteria)

    return {
        **get_base_data(guideline, "guideline", version),
        # Content
        "description": description,
        # Hierarchy
        **get_parent_data("principle", principle),
        # Success Criteria for this guideline
        "success_criteria_count": success_criteria_count,
        "success_criteria_ids": success_criteria_ids,
        # Metadata
        "full_context": f"WCAG {version} {principle.num}.{guideline.num}: {guideline.title} (under {principle.num}. {principle.title})",
    }


def make_success_criteria_chunk(
    success_criteria: Successcriterion,
    guideline: Guideline,
    principle: Principle,
    wcag_version: WcagVersion,
    wcag_data: WCAGData,
):
    description = clean_wcag_text(success_criteria.content)

    return {
        **get_base_data(success_criteria, "success_criterion", wcag_version),
        # Content
        "description": description,
        # Hierarchy
        **get_parent_data("guideline", guideline),
        "principle_id": principle.id,
        "principle_num": principle.num,
        "principle_title": principle.title,
        "versions_applicable": success_criteria.versions,
        "techniques": extract_techniques_summary(success_criteria.techniques),
        # Compliance / testing
        "compliance_level": success_criteria.level,
        "testing_requirements": extract_testing_requirements(success_criteria),
        # Metadata
        "full_context": f"WCAG {wcag_version} Success Criterion {success_criteria.num} ({success_criteria.level}): {description}",
        "related_requirements": find_related_requirements(success_criteria, wcag_data),
    }


def make_term_chunk(term: Term, version: str) -> TermChunk:
    definition = clean_wcag_text(term.definition)

    return {
        "chunk_id": f"term_{term.id}",
        "type": "definition",
        "wcag_version": version,
        "id": term.id,
        "term": term.name,
        "definition": definition,
        "level": "definition",
        "full_context": f"WCAG {version} Definition: {term.name}",
    }


def preprocess_wcag_data(wcag_version: WcagVersion = "2.2") -> list[dict[str, Any]]:
    wcag_data = get_wcag_data(wcag_version)
    chunks = []

    for principle in wcag_data.principles:
        chunks.append(make_principle_chunk(principle, wcag_version))
        for guideline in principle.guidelines:
            chunks.append(make_guideline_chunk(guideline, principle, wcag_version))
            for sc in guideline.successcriteria:
                chunks.append(
                    make_success_criteria_chunk(
                        sc, guideline, principle, wcag_version, wcag_data
                    )
                )

    # Add terms/definitions
    for term in wcag_data.terms:
        chunks.append(make_term_chunk(term, wcag_version))

    return chunks


def save_preprocessed_data(chunks: list[dict[str, Any]], version: WcagVersion = "2.2"):
    """Save preprocessed data to a file."""
    output_file = PROCESSED_DIR / f"wcag-{version}_preprocessed.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(chunks)} chunks to {output_file}")
    return output_file


# Main execution
if __name__ == "__main__":
    # Preprocess both versions
    for wcag_version in ["2.1", "2.2"]:
        print(f"\nProcessing WCAG {wcag_version}...")
        chunks = preprocess_wcag_data(wcag_version)
        PROCESSED_DIR.mkdir(exist_ok=True)
        save_preprocessed_data(chunks, wcag_version)

        # Print summary
        types = {}
        for chunk in chunks:
            chunk_type = chunk.get("type", "unknown")
            types[chunk_type] = types.get(chunk_type, 0) + 1

        print(f"  Total chunks: {len(chunks)}")
        for chunk_type, count in types.items():
            print(f"  {chunk_type}: {count}")
