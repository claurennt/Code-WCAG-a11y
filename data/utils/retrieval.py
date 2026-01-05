from typing import Any, Dict, List
from utils.formatter import clean_wcag_text


def get_chunk_by_id(chunks: List[Dict[str, Any]], chunk_id: str) -> Dict[str, Any]:
    """Retrieve a specific chunk by its ID."""
    for chunk in chunks:
        if chunk.get("chunk_id") == chunk_id:
            return chunk
    return {}


def get_related_chunks(
    chunks: List[Dict[str, Any]], parent_id: str = None, chunk_type: str = None
) -> List[Dict[str, Any]]:
    """Get chunks filtered by parent ID or type."""
    filtered = []
    for chunk in chunks:
        if parent_id and chunk.get("parent_id") == parent_id:
            filtered.append(chunk)
        elif chunk_type and chunk.get("type") == chunk_type:
            filtered.append(chunk)
    return filtered


def find_related_requirements(
    sc: Dict[str, Any], wcag_data: Dict[str, Any]
) -> List[str]:
    """Find related success criteria based on content similarity."""
    related = []
    sc_id = sc.get("id")
    sc_content = clean_wcag_text(sc.get("content", "").lower())

    # Simple keyword-based relation - can be enhanced with embeddings later
    keywords = set(sc_content.split()[:10])

    for principle in wcag_data.get("principles", []):
        for guideline in principle.get("guidelines", []):
            for other_sc in guideline.get("successcriteria", []):
                if other_sc.get("id") == sc_id:
                    continue  # Skip self

                other_content = clean_wcag_text(other_sc.get("content", "").lower())
                other_keywords = set(other_content.split()[:10])

                # If they share at least 3 keywords, consider them related
                common = keywords.intersection(other_keywords)
                if len(common) >= 3:
                    related.append(other_sc.get("num"))

    return related
