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
from code_wcag_a11y.scripts.utils.scrape_wcag_website import (
    get_sc_url,
    get_user_benefits_from_rule_page,
    load_benefits_cache,
    save_benefits_cache,
)
from code_wcag_a11y.utils.logger import logger
from code_wcag_a11y.globals import BENEFITS_CACHE_FILE, PROCESSED_DIR, RAW_DIR


WCAG_VERSIONS = ["2.1", "2.2"]
UNDERSTANDING_DOCS_BASE_URL = "https://www.w3.org/WAI"


def get_wcag_data(wcag_version: WcagVersion = "2.1") -> WCAGData:
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


def preprocess_wcag_data(
    wcag_version: WcagVersion = "2.1", cache: dict[str, list[str]] = None
) -> list[dict[str, Any]]:
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
                # AUTO-DETECTION: If ID isn't in cache, we scrape it once.
                if sc.id not in cache:
                    logger.info(f"🌐 New SC found: {sc.id}. Scraping benefits...")
                    sc_url = get_sc_url(
                        UNDERSTANDING_DOCS_BASE_URL, sc.id, wcag_version
                    )
                    benefits = get_user_benefits_from_rule_page(sc_url)
                    cache[sc.id] = benefits
                else:
                    benefits = cache[sc.id]
                    sc_chunk = {
                        **get_base_data(sc, "success_criterion", wcag_version),
                        **get_parent_data("guideline", guideline),
                        "text": make_sc_consolidated_text(
                            sc, principle, guideline, benefits
                        ),
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

    # 1. Handle Deletion Flags
    if args.delete_processed and PROCESSED_DIR.exists():

        for file in PROCESSED_DIR.glob("*.json"):
            file.unlink()
        logger.info(f"🗑️ Deleted existing processed files")

    if args.delete_benefits and BENEFITS_CACHE_FILE.exists():
        BENEFITS_CACHE_FILE.unlink()
        logger.info(f"🗑️ Deleted benefits cache: {BENEFITS_CACHE_FILE}")

    # Ensure processed directory exists for output
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Load the cache (will be empty if deleted or first run)
    benefits_cache = load_benefits_cache()
    initial_cache_size = len(benefits_cache)

    # 3. Process Versions
    # - Use cache if available (satisfies requirement 4)
    # - Scrape and add to cache if missing/deleted
    for version in WCAG_VERSIONS:
        logger.info(f"🚀 Processing WCAG {version}...")
        chunks = preprocess_wcag_data(version, benefits_cache)
        save_preprocessed_data(chunks, version)

    # 4. Save the cache back to disk (Updated with new scrapes)
    if len(benefits_cache) > initial_cache_size:
        save_benefits_cache(benefits_cache)
        logger.info(
            f"💾 Cache updated: {initial_cache_size} -> {len(benefits_cache)} entries."
        )
    else:
        logger.info(
            f"✅ No new scrapes needed. Used existing cache of {len(benefits_cache)} entries."
        )
