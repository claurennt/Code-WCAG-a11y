import hashlib
from pathlib import Path
from typing import Literal, Dict, Any, List
import json
import re
from utils.index import (
    clean_wcag_text,
    get_base_data,
    get_parent_data,
    extract_techniques_summary,
    extract_testing_requirements,
)

BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(exist_ok=True)

WcagVersion = Literal["21", "22"]


def get_wcag_data(version: WcagVersion = "22") -> Dict[str, Any]:
    """Load and parse WCAG JSON data."""
    file_path = BASE_DIR / f"wcag-{version}.json"
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def make_principle_chunk(principle: Dict[str, Any], version: str) -> Dict[str, Any]:
    description = clean_wcag_text(principle.get("content", ""))
    return {
        **get_base_data(principle, "principle", version),
        "description": description,
        "guidelines_count": len(principle.get("guidelines", [])),
        "guideline_ids": [g.get("id") for g in principle.get("guidelines", [])],
        "content_hash": hashlib.sha256(description.encode("utf-8")).hexdigest(),
        "full_context": f"WCAG {version} Principle {principle.get('num')}: {principle.get('title')}",
    }


def make_guideline_chunk(
    guideline: Dict[str, Any], principle: Dict[str, Any], version: str
) -> Dict[str, Any]:
    description = clean_wcag_text(guideline.get("content", ""))
    return {
        **get_base_data(guideline, "guideline", version),
        "description": description,
        **get_parent_data("principle", principle),
        "success_criteria_count": len(guideline.get("successcriteria", [])),
        "success_criteria_ids": [
            sc.get("id") for sc in guideline.get("successcriteria", [])
        ],
        "full_context": f"WCAG {version} {principle.get('num')}.{guideline.get('num')}: {guideline.get('title')} (under {principle.get('num')}. {principle.get('title')})",
    }


def make_sc_chunk(
    sc: Dict[str, Any],
    guideline: Dict[str, Any],
    principle: Dict[str, Any],
    version: str,
    wcag_data: Dict[str, Any],
) -> Dict[str, Any]:
    description = clean_wcag_text(sc.get("content", ""))
    return {
        **get_base_data(sc, "success_criterion", version),
        "description": description,
        **get_parent_data("guideline", guideline),
        "principle_id": principle.get("id"),
        "principle_num": principle.get("num"),
        "principle_title": principle.get("title"),
        "versions_applicable": sc.get("versions", []),
        "techniques": extract_techniques_summary(sc.get("techniques", {})),
        "compliance_level": sc.get("level", ""),
        "testing_requirements": extract_testing_requirements(sc),
        "full_context": f"WCAG {version} Success Criterion {sc.get('num')} ({sc.get('level')}): {sc.get('title')}",
        "related_requirements": find_related_requirements(sc, wcag_data),
    }


def make_term_chunk(term: Dict[str, Any], version: str) -> Dict[str, Any]:
    return {
        "chunk_id": f"term_{term.get('id')}",
        "type": "definition",
        "wcag_version": version,
        "id": term.get("id"),
        "term": term.get("name"),
        "definition": clean_wcag_text(term.get("definition", "")),
        "level": "definition",
        "full_context": f"WCAG {version} Definition: {term.get('name')}",
    }


def preprocess_wcag_data(version: str = "22") -> List[Dict[str, Any]]:
    wcag_data = get_wcag_data(version)
    chunks: List[Dict[str, Any]] = []

    for principle in wcag_data.get("principles", []):
        chunks.append(make_principle_chunk(principle, version))
        for guideline in principle.get("guidelines", []):
            chunks.append(make_guideline_chunk(guideline, principle, version))
            for sc in guideline.get("successcriteria", []):
                chunks.append(
                    make_sc_chunk(sc, guideline, principle, version, wcag_data)
                )

    # Add terms/definitions
    for term in wcag_data.get("terms", []):
        chunks.append(make_term_chunk(term, version))

    return chunks


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

    return related[:5]  # Limit to 5 most related


def save_preprocessed_data(chunks: List[Dict[str, Any]], version: WcagVersion = "22"):
    """Save preprocessed data to a file."""
    output_file = STORAGE_DIR / f"wcag_{version}_preprocessed.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(chunks)} chunks to {output_file}")
    return output_file


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


# Main execution
if __name__ == "__main__":
    # Preprocess both versions
    for version in ["21", "22"]:
        print(f"\nProcessing WCAG {version}...")
        chunks = preprocess_wcag_data(version)  # type: ignore
        save_preprocessed_data(chunks, version)  # type: ignore

        # Print summary
        types = {}
        for chunk in chunks:
            chunk_type = chunk.get("type", "unknown")
            types[chunk_type] = types.get(chunk_type, 0) + 1

        print(f"  Total chunks: {len(chunks)}")
        for chunk_type, count in types.items():
            print(f"  {chunk_type}: {count}")
