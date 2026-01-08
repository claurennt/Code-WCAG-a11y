from typing import Union
import re

from ..types.wcag_types import (
    AdvisoryItem,
    FailureItem,
    Guideline,
    Principle,
    Successcriterion,
    SufficientItem,
    Techniques,
)
from ..types.chunk_types import BaseData, ParentData, WcagVersion


TechniqueItem = Union[SufficientItem, AdvisoryItem, FailureItem]


def clean_wcag_text(text: str) -> str:
    """Clean HTML and normalize text."""
    if not text:
        return ""

    # Remove HTML tags
    text = re.sub(r"<[^>]*>", " ", text)

    # Remove spaces before punctuation
    text = re.sub(r"\s+([.,;:!?)\]}>])", r"\1", text)

    # Decode HTML entities
    import html

    text = html.unescape(text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def get_base_data(
    type: Union[Principle, Guideline, Successcriterion],
    type_name: str,
    wcag_version: WcagVersion,
) -> BaseData:
    return {
        "chunk_id": f"{type_name}_{type.id}",
        "wcag_version": wcag_version,
        "id": type.id,
        "level": type.level if isinstance(type, Successcriterion) else type_name,
        "num": type.num,
        "handle": type.handle,
        "type": type_name,
    }


def get_parent_data(
    parent_type: str, parent: Union[Principle, Guideline]
) -> ParentData:
    return {
        "parent_id": parent.id,
        "parent_type": parent_type,
        "parent_num": parent.num,
        "parent_title": parent.title,
    }


def extract_techniques_summary(techniques: Techniques) -> dict[str, list[str]]:
    if not techniques:
        return {}

    summary: dict[str, list[str]] = {}

    if techniques.sufficient:
        summary["sufficient"] = []
        for item in techniques.sufficient:
            summary["sufficient"].extend(format_technique_item(item))

    if techniques.advisory:
        summary["advisory"] = []
        for item in techniques.advisory:
            summary["advisory"].extend(format_technique_item(item))

    if techniques.failure:
        summary["failure"] = []
        for item in techniques.failure:
            summary["failure"].extend(format_technique_item(item))

    if techniques.sufficientNote:
        summary["sufficientNote"] = [clean_wcag_text(techniques.sufficientNote)]

    return summary


def get_sub_items(item: TechniqueItem) -> list[TechniqueItem]:
    """Return all sub-items from 'using' or 'and_' for recursion."""
    using = getattr(item, "using", None) or []
    and_ = getattr(item, "and_", None) or []
    return using + and_


def format_technique_item(item: TechniqueItem) -> list[str]:
    """Recursively format a technique item into a list of strings."""
    lines: list[str] = []

    if item.title:
        line = f"{item.id}: {item.title}" if item.id else item.title
        lines.append(clean_wcag_text(line))

    for sub_item in get_sub_items(item):
        lines.extend(format_technique_item(sub_item))

    return lines


def extract_testing_requirements(success_criterion: Successcriterion) -> list[str]:
    """Extract testing requirements from success criterion."""
    requirements = []
    description = clean_wcag_text(success_criterion.content).lower()

    # Extract key testing phrases
    test_phrases = [
        "must be",
        "shall",
        "required",
        "should",
        "can be",
        "cannot",
        "must not",
    ]

    # Simple extraction
    for phrase in test_phrases:
        if phrase in description:
            # Find the sentence containing the phrase
            sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", description)
            for sentence in sentences:
                if phrase in sentence.lower():
                    requirements.append(sentence.strip())

    return requirements
