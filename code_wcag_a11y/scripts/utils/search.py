from typing import List
from chromadb.api.types import QueryResult

from code_wcag_a11y.scripts.types.chunk_types import SearchResult


def filter_results_by_distance(
    results: QueryResult, threshold: float
) -> List[SearchResult]:
    final_results = []

    # Handle empty case
    if not results or not results["ids"] or not results["ids"][0]:
        return []

    for i in range(len(results["ids"][0])):
        dist = results["distances"][0][i]
        print(dist)
        if dist < threshold:
            print(results["ids"][0][i])
            final_results.append(results["documents"][0][i])

    return final_results
