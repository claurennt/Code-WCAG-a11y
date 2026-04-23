import re
from typing import List

from code_wcag_a11y.scripts.chromadb import get_collection
from code_wcag_a11y.scripts.types.chunk_types import SearchResult, WcagVersion
from code_wcag_a11y.scripts.utils.search import filter_results_by_distance
from code_wcag_a11y.utils.logger import logger

import re
from typing import List
from code_wcag_a11y.scripts.chromadb import get_collection
from code_wcag_a11y.scripts.types.chunk_types import SearchResult, WcagVersion
from code_wcag_a11y.scripts.utils.search import filter_results_by_distance
from code_wcag_a11y.utils.logger import logger


def search_wcag(
    query: str,
    wcag_version: WcagVersion = "2.1",
    distance_threshold: float = 0.5,
) -> List[SearchResult]:
    """Search WCAG guidelines using vector similarity and return flattened results."""
    try:
        collection = get_collection(wcag_version)

        # Increase n_results to 10 to ensure we have content after filtering
        results = collection.query(
            query_texts=[query],
            n_results=86,
            where={"type": "success_criterion"},
        )

        return filter_results_by_distance(results, distance_threshold)

    except Exception as e:
        logger.error(f"❌ Search failed: {e}")
        raise


if __name__ == "__main__":
    test_query = "What WCAG SUCCESS CRITERIA mention screen readers?"

    matches = search_wcag(test_query)
    # print(matches)
    # Direct access to the list! No matches[0] or complex parsing needed.
    for i, match in enumerate(matches):
        print(f"-- Result {i}")
        print(f"ID: {match}")
