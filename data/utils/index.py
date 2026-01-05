from typing import Dict, Any, Literal, List

import re

WcagVersion = Literal["21", "22"]


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


def get_base_data(type: Dict, type_name: str, version: str) -> Dict[str, str]:
    return {
        "chunk_id": f"{type_name}_{type.get('id')}",
        "wcag_version": version,
        "id": type.get("id"),
        "level": type.get("level") or type_name,
        "num": type.get("num"),
        "handle": type.get("handle"),
        "type": type_name,
    }


def get_parent_data(parent_type: str, parent: Dict) -> Dict[str, str]:
    return {
        "parent_id": parent.get("id"),
        "parent_type": parent_type,
        "parent_num": parent.get("num"),
        "parent_title": parent.get("title"),
    }


def extract_techniques_summary(techniques: Dict[str, Any]) -> Dict[str, List[str]]:
    """Extract and format techniques while preserving logical structure."""
    if not techniques:
        return {}

    summary: Dict[str, List[str]] = {}

    for category, items in techniques.items():

        if not items:
            continue

        summary[category] = []
        if category == "sufficientNote":
            summary[category] = [clean_wcag_text(items)]
            continue
        for item in items:

            summary[category].extend(format_technique_item(item))

    return summary


def format_technique_item(item: Dict[str, Any], indent: int = 0) -> List[str]:
    lines = []
    prefix = "  " * indent

    # Case 1: Simple technique with ID
    if "id" in item and "title" in item:
        lines.append(f"{prefix}{item['id']}: {item['title']}")
        return lines

    # Case 2: Title-only node (section header)
    if "title" in item and "using" in item:
        for sub in item["using"]:
            if "id" in sub:
                lines.extend(format_technique_item(sub, indent + 1))
        return lines

    # Case 3: Logical AND
    if "and" in item:
        for sub in item["and"]:
            if "id" in sub:
                lines.extend(format_technique_item(sub, indent + 1))
        return lines

    # Case 4: Using one or more techniques
    if "using" in item:
        for sub in item["using"]:
            if "id" in sub:
                lines.extend(format_technique_item(sub, indent + 1))
        return lines

    # Fallback
    if "title" in item:
        lines.append(f"{prefix}{clean_wcag_text(item['title'])}")

    return lines


def extract_testing_requirements(sc: Dict[str, Any]) -> List[str]:
    """Extract testing requirements from success criterion."""
    requirements = []
    description = clean_wcag_text(sc.get("content", ""))

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

    # Simple extraction - you can enhance this
    for phrase in test_phrases:
        if phrase in description.lower():
            # Find the sentence containing the phrase
            sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", description)
            for sentence in sentences:
                if phrase in sentence.lower():
                    requirements.append(sentence.strip())

    return requirements
