from typing import Optional
from code_wcag_a11y.utils.formatter import clean_wcag_text
from code_wcag_a11y.types.wcag_types import Successcriterion, WCAGData


def get_chunk_by_id(chunks: list[dict], chunk_id: str) -> dict:
    """
    Retrieve a specific chunk by its ID.

    Args:
        chunks: Preprocessed WCAG chunks (dicts).
        chunk_id: The chunk_id to search for.

    Returns:
        The chunk dict if found, else empty dict.
    """
    return next((chunk for chunk in chunks if chunk.id == chunk_id), {})


def get_related_chunks(
    chunks: list[dict],
    parent_id: Optional[str] = None,
    chunk_type: Optional[str] = None,
) -> list[dict]:
    """
    Get chunks filtered by parent ID or type.

    Args:
        chunks: List of preprocessed chunk dicts.
        parent_id: Optional parent_id to filter on.
        chunk_type: Optional type to filter on.

    Returns:
        List of matching chunk dicts.
    """
    filtered: list[dict] = []
    for chunk in chunks:
        if parent_id is not None and chunk.get("parent_id") == parent_id:
            filtered.append(chunk)
        elif chunk_type is not None and chunk.get("type") == chunk_type:
            filtered.append(chunk)
    return filtered


def find_related_requirements(
    success_criterion: Successcriterion,
    wcag_data: WCAGData,
    min_common_keywords: int = 3,
) -> list[str]:
    """
    Find related success criteria based on shared keywords.

    Args:
        sc: The success criterion to find relations for.
        wcag_data: List of all principles (typed).
        min_common_keywords: Minimum number of shared keywords to consider related.

    Returns:
        List of SC numbers that are related.
    """
    related: list[str] = []
    success_criterion_id = success_criterion.id
    success_criterion_content = clean_wcag_text(success_criterion.content).lower()

    # Take first 10 words as keywords
    keywords = set(success_criterion_content.split()[:10])

    for principle in wcag_data.principles:
        for guideline in principle.guidelines:
            for other_success_criterion in guideline.successcriteria:
                if other_success_criterion.id == success_criterion_id:
                    continue  # skip self

                other_content = clean_wcag_text(other_success_criterion.content).lower()
                other_keywords = set(other_content.split()[:10])

                if len(keywords.intersection(other_keywords)) >= min_common_keywords:
                    related.append(other_success_criterion.num)
    return related
