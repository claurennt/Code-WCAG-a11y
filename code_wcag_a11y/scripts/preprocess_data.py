import json
from pathlib import Path
from typing import Any

from code_wcag_a11y.scripts.types.chunk_types import WcagVersion
from code_wcag_a11y.scripts.utils.cli_utils import setup_delete_parser
from code_wcag_a11y.scripts.utils.preprocess import (
    clean_wcag_text,
    extract_techniques_summary,
    get_base_data,
    get_parent_data,
    make_sc_consolidated_text,
)
from code_wcag_a11y.scripts.types.wcag_types import WCAGData
from code_wcag_a11y.utils.logger import logger
from code_wcag_a11y.globals import PROCESSED_DIR, RAW_DIR


WCAG_VERSIONS = ["2.1", "2.2"]


def get_wcag_data(wcag_version: WcagVersion = "2.2") -> WCAGData:
    """Load and parse WCAG JSON data.

    Args:
        wcag_version: WCAG version to load (e.g., "2.1" or "2.2").

    Returns:
        Validated WCAGData object.

    Raises:
        FileNotFoundError: If the WCAG JSON file doesn't exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """

    file_path = RAW_DIR / f"wcag-{wcag_version}.json"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"❌ WCAG file not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON in {file_path}: {e}")
        raise

    return WCAGData.model_validate(data)


def preprocess_wcag_data(wcag_version: WcagVersion = "2.2") -> list[dict[str, Any]]:
    # 1. Load data using your Pydantic Model
    wcag_data = get_wcag_data(wcag_version)

    chunks = []

    for principle in wcag_data.principles:
        # Principle Chunk
        chunks.append(
            {
                **get_base_data(principle, "principle", wcag_version),
                "description": clean_wcag_text(principle.content),
            }
        )

        for guideline in principle.guidelines:
            # Guideline Chunk
            chunks.append(
                {
                    **get_base_data(guideline, "guideline", wcag_version),
                    **get_parent_data("principle", principle),
                    "description": clean_wcag_text(guideline.content),
                }
            )

            for sc in guideline.successcriteria:
                # Success Criterion Chunk
                sc_chunk = {
                    **get_base_data(sc, "success_criterion", wcag_version),
                    **get_parent_data("guideline", guideline),
                    "text": make_sc_consolidated_text(sc, principle, guideline),
                    "metadata": {
                        "level": sc.level,
                        "techniques": extract_techniques_summary(sc.techniques),
                    },
                }
                chunks.append(sc_chunk)

    # Definitions
    for term in wcag_data.terms:
        chunks.append(
            {
                **get_base_data(term, "definition", wcag_version),
                "text": f"Definition: {term.name} - {clean_wcag_text(term.definition)}",
            }
        )

    return chunks


def save_preprocessed_data(
    chunks: list[dict[str, Any]], version: WcagVersion = "2.2"
) -> Path:
    """Save preprocessed data to a file.

    Args:
        chunks: List of preprocessed chunk dictionaries.
        version: WCAG version string.

    Returns:
        Path to the saved file.
    """
    output_file = PROCESSED_DIR / f"wcag-{version}_preprocessed.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    logger.debug(f"Saved {len(chunks)} chunks to {output_file}")
    return output_file


# Main execution
if __name__ == "__main__":
    args = setup_delete_parser()

    if args.delete:
        if PROCESSED_DIR.exists():
            import shutil

            logger.debug(f"Deleting all existing processed data in {PROCESSED_DIR}...")
            # We use ignore_errors=True to handle cases where files are locked
            shutil.rmtree(PROCESSED_DIR, ignore_errors=True)

    # Preprocess all versions
    for wcag_version in WCAG_VERSIONS:
        logger.debug(f"\nProcessing WCAG {wcag_version}...")
        chunks = preprocess_wcag_data(wcag_version)
        PROCESSED_DIR.mkdir(exist_ok=True)
        save_preprocessed_data(chunks, wcag_version)

        # Print summary
        types = {}
        for chunk in chunks:
            chunk_type = chunk.get("type", "unknown")
            types[chunk_type] = types.get(chunk_type, 0) + 1

        logger.info(f"  Total chunks: {len(chunks)}")
        for chunk_type, count in types.items():
            logger.info(f"{chunk_type}: {count}")
