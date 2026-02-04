from typing import Union
import re

from ..types.wcag_types import (
    AdvisoryItem,
    FailureItem,
    Guideline,
    Principle,
    Successcriterion,
    SufficientItem,
    Term,
)
from ..types.chunk_types import BaseData, ParentData, WcagVersion


TechniqueItem = Union[SufficientItem, AdvisoryItem, FailureItem]


def clean_wcag_text(text: str) -> str:
    """Clean HTML and normalize text."""
    if not text:
        return ""

    # Remove HTML tags
    text = re.sub(r"<[^>]*>", " ", text)

    # Decode HTML entities
    import html

    text = html.unescape(text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def get_base_data(
    type: Union[Principle, Guideline, Successcriterion, Term],
    type_name: str,
    wcag_version: WcagVersion,
) -> BaseData:

    base = {
        "chunk_id": f"{type_name}_{type.id}",
        "wcag_version": wcag_version,
        "id": type.id,
        "type": type_name,
    }

    if hasattr(type, "num"):
        base["num"] = type.num

    if hasattr(type, "handle"):
        base["handle"] = type.handle

    if hasattr(type, "level"):
        base["level"] = type.level
    else:
        base["level"] = type_name

    return base


def get_parent_data(
    parent_type: str, parent: Union[Principle, Guideline]
) -> ParentData:

    return {
        "parent_id": parent.id,
        "parent_type": parent_type,
        "parent_num": parent.num,
        "parent_title": parent.handle,  # Using handle as title per your JSON keys
    }


def extract_techniques_summary(techniques: TechniqueItem) -> dict[str, list[str]]:
    """Restored original signature and logic."""
    if not techniques:
        return {}

    summary: dict[str, list[str]] = {}

    # Check and format each category
    categories = ["sufficient", "advisory", "failure"]
    for cat in categories:
        items = getattr(techniques, cat, None)
        if items:
            summary[cat] = format_technique_item(items)

    if getattr(techniques, "sufficientNote", None):
        summary["sufficientNote"] = [clean_wcag_text(techniques.sufficientNote)]

    return summary


def format_technique_item(item: TechniqueItem) -> list[str]:

    lines: list[str] = []

    if isinstance(item, list):
        for sub in item:
            lines.extend(format_technique_item(sub))
        return lines

    title = getattr(item, "title", None)
    if title:
        tech_id = getattr(item, "id", None)
        suffix = getattr(item, "suffix", None)
        line = f"{tech_id}: {title}" if tech_id else title
        if suffix:
            line = f"{line} {suffix}"
        lines.append(clean_wcag_text(line))

    # Recursive check for nested structures (Groups, Techniques, logical children)
    for attr in ("techniques", "groups", "using", "and_"):
        children = getattr(item, attr, None)
        if children:
            lines.extend(format_technique_item(children))

    return lines


def make_sc_consolidated_text(
    sc: Successcriterion, principle: Principle, guideline: Guideline
) -> str:
    """
    Internal helper to create a rich 'text' field for RAG.
    This ensures the embedding captures the Rule + Pass/Fail criteria.
    """
    tech_summary = extract_techniques_summary(sc.techniques)

    body = [
        f"WCAG Success Criterion {sc.num}: {sc.handle} (Level {sc.level})",
        f"Principle: {principle.handle} / Guideline: {guideline.handle}",
        f"Requirement: {clean_wcag_text(sc.content)}",
        "\nSufficient Techniques (Ways to Pass):",
        "\n".join(tech_summary.get("sufficient", [])),
        "\nCommon Failures (QA Checkpoints):",
        "\n".join(tech_summary.get("failure", [])),
    ]
    return "\n".join(filter(None, body))
