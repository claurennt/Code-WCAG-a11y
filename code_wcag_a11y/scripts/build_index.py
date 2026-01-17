#!/usr/bin/env python3

import json
from pathlib import Path

from llama_index.core import (
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
    Settings,
    Document,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

from code_wcag_a11y.globals import INDICES_DIR, PROCESSED_DIR
from code_wcag_a11y.scripts.types.chunk_types import WcagVersion

from .utils.index import create_document_metadata, create_embedding_text
from code_wcag_a11y.utils.logger import logger

Settings.llm = Ollama(
    model="llama3:latest",
    request_timeout=120.0,
    context_window=8000,
)

Settings.embed_model = OllamaEmbedding(
    model_name="nomic-embed-text",
)


def load_existing_index(persist_dir: Path) -> VectorStoreIndex | None:
    index_store_file = persist_dir / "index_store.json"

    if not index_store_file.exists():
        return None

    logger.info("Loading existing index from disk...")
    storage_context = StorageContext.from_defaults(persist_dir=str(persist_dir))
    return load_index_from_storage(storage_context)


def build_and_persist_index(
    data_file: Path,
    persist_dir: Path,
    wcag_version: WcagVersion,
) -> VectorStoreIndex:
    logger.info(f"Creating new index for WCAG {wcag_version}...")

    with open(data_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    documents = [
        Document(
            text=create_embedding_text(chunk),
            metadata=create_document_metadata(chunk),
        )
        for chunk in chunks
    ]

    splitter = SentenceSplitter(
        chunk_size=512,
        chunk_overlap=50,
        include_metadata=True,
        include_prev_next_rel=True,
    )

    nodes = splitter.get_nodes_from_documents(documents)
    index = VectorStoreIndex(nodes)

    index.storage_context.persist(persist_dir=str(persist_dir))

    logger.info(f"Created index with {len(nodes)} nodes")
    return index


def get_index(wcag_version: WcagVersion = "2.2") -> VectorStoreIndex:
    data_file = PROCESSED_DIR / f"wcag-{wcag_version}_preprocessed.json"
    if not data_file.exists():
        raise FileNotFoundError(f"Processed data file not found: {data_file}")

    persist_dir = INDICES_DIR / f"wcag-{wcag_version}" / "vector_storage"
    persist_dir.mkdir(parents=True, exist_ok=True)

    index = load_existing_index(persist_dir)

    if not index:
        return build_and_persist_index(data_file, persist_dir, wcag_version)

    return index


def build_all_indices():
    """Build indices for all available WCAG versions."""
    logger.info("Building WCAG indices...")

    available_versions = []
    for wcag_version in ["2.1", "2.2"]:
        data_file = PROCESSED_DIR / f"wcag-{wcag_version}_preprocessed.json"
        if data_file.exists():
            available_versions.append(wcag_version)
        else:
            logger.warning(f"No processed data for WCAG {wcag_version}")

    if not available_versions:
        logger.error("No processed data files found")
        return None

    indices = {}
    for wcag_version in available_versions:
        try:
            index = get_index(wcag_version=wcag_version)
            indices[wcag_version] = index
            logger.info(f"✓ WCAG {wcag_version} done")
        except Exception as e:
            logger.error(f"✗ WCAG {wcag_version} failed: {e}")

    return indices


# Main execution
if __name__ == "__main__":
    # Ensure indices directory exists
    INDICES_DIR.mkdir(parents=True, exist_ok=True)

    # Build all available indices
    indices = build_all_indices()

    if indices:
        logger.info(f"Built {len(indices)} index(es)")
    else:
        logger.error("No indices built")
