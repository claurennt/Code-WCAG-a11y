from code_wcag_a11y.scripts.chromadb import collection
from code_wcag_a11y.utils.logger import logger


def search_wcag(query: str, n_results: int = 5):

    results = collection.query(query_texts=[query], n_results=n_results)
    return results


if __name__ == "__main__":
    test_query = "What are the rules for a custom HTML button without correct role?"
    matches = search_wcag(test_query)
    logger.info(f"\nTop Match: {matches['documents']}...")
