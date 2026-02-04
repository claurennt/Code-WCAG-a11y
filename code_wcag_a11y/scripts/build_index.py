import json
from pathlib import Path
from typing import List, Dict


from code_wcag_a11y.globals import CHROMADB_WCAG_PATH, PROCESSED_DIR
from code_wcag_a11y.scripts.utils.cli_utils import setup_delete_parser
from code_wcag_a11y.scripts.chromadb import collection
from code_wcag_a11y.utils.logger import logger


def index_wcag_files(file_path: Path):

    # Load JSON
    with open(file_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    ids = []
    documents = []
    metadatas = []

    for chunk in chunks:

        # Use the text or description field for the vector search
        ids.append(chunk["chunk_id"])
        content = chunk.get("text") or chunk.get("description")
        documents.append(content)

        # Flatten metadata for ChromaDB compatibility
        meta = {
            "version": chunk.get("wcag_version", "unknown"),
            "level": chunk.get("level", "N/A"),
            "type": chunk.get("type", "unknown"),
            "handle": chunk.get("handle", "unknown"),
        }
        metadatas.append(meta)

    collection.add(ids=ids, documents=documents, metadatas=metadatas)

    logger.info(f"✅ Success: Indexed {len(documents)} chunks locally.")


if __name__ == "__main__":

    args = setup_delete_parser()

    if args.delete:
        if CHROMADB_WCAG_PATH.exists():
            import shutil

            shutil.rmtree(CHROMADB_WCAG_PATH, ignore_errors=True)
            logger.info("✅ Deleted existing indices.")

    for version in ["2.1", "2.2"]:
        DATA_FILE = f"{PROCESSED_DIR}/wcag-{version}_preprocessed.json"
        logger.info(f"--- Indexing WCAG {version} from {DATA_FILE} ---")
        index_wcag_files(Path(DATA_FILE))
