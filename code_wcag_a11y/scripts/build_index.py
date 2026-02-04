import json
import shutil
from pathlib import Path

from huggingface_hub import Collection

from code_wcag_a11y.globals import CHROMADB_WCAG_PATH, PROCESSED_DIR
from code_wcag_a11y.scripts.utils.cli_utils import setup_delete_parser
from code_wcag_a11y.utils.logger import logger
from code_wcag_a11y.scripts.chromadb import get_collection


def index_wcag_files(file_path: Path, collection: Collection) -> None:
    """Index WCAG JSON chunks into ChromaDB.

    Args:
        file_path: Path to the preprocessed WCAG JSON file.

    Raises:
        FileNotFoundError: If the file_path does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not file_path.exists():
        logger.error(f"❌ File not found: {file_path}")
        raise FileNotFoundError(f"WCAG data file not found: {file_path}")

    # Load JSON
    with open(file_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    ids = []
    documents = []
    metadatas = []

    for chunk in chunks:
        # Validate required fields
        if "chunk_id" not in chunk:
            logger.warning(f"⚠️ Missing 'chunk_id' in chunk, skipping...")
            continue

        content = chunk.get("text") or chunk.get("description")
        if not content:
            logger.warning(
                f"⚠️ Missing content in chunk {chunk.get('chunk_id')}, skipping..."
            )
            continue

        # Use the text or description field for the vector search
        ids.append(chunk["chunk_id"])
        documents.append(content)

        # Flatten metadata for ChromaDB compatibility
        meta = {
            "version": chunk.get("wcag_version", "unknown"),
            "level": chunk.get("level", "N/A"),
            "type": chunk.get("type", "unknown"),
            "handle": chunk.get("handle", "unknown"),
        }
        metadatas.append(meta)

    if not ids:
        logger.warning(f"⚠️ No valid chunks found in {file_path}")
        return

    collection = get_collection()
    collection.add(ids=ids, documents=documents, metadatas=metadatas)

    logger.info(f"✅ Success: Indexed {len(documents)} chunks from {file_path.name}.")


def delete_chroma_db() -> bool:
    """Delete the ChromaDB index directory.

    Returns:
        True if deletion was successful, False otherwise.
    """
    if not CHROMADB_WCAG_PATH.exists():
        logger.info("ℹ️ No existing Chroma DB to delete.")
        return True

    logger.info(f"🧹 Deleting Chroma DB at {CHROMADB_WCAG_PATH}")
    try:
        shutil.rmtree(CHROMADB_WCAG_PATH)
        logger.info("✅ Deleted existing indices.")
        return True
    except OSError as e:
        logger.error(f"❌ Failed to delete Chroma DB: {e}")
        return False


if __name__ == "__main__":
    args = setup_delete_parser()

    if args.delete:
        delete_chroma_db()

    # Configurable WCAG versions
    WCAG_VERSIONS = ["2.1", "2.2"]

    for version in WCAG_VERSIONS:
        data_file = Path(PROCESSED_DIR) / f"wcag-{version}_preprocessed.json"
        logger.info(f"--- Indexing WCAG {version} from {data_file} ---")
        try:
            collection = get_collection()
            index_wcag_files(data_file, collection)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"❌ Failed to index WCAG {version}: {e}")
