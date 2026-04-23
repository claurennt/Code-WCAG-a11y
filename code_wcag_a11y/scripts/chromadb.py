import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from code_wcag_a11y.globals import CHROMADB_WCAG_PATH
from code_wcag_a11y.scripts.types.chunk_types import WcagVersion


def get_vector_client(path: str):
    return chromadb.PersistentClient(path=path)


def get_embedding_model():
    return SentenceTransformerEmbeddingFunction(model_name="all-mpnet-base-v2")


def create_collection_name(wcag_version: WcagVersion = "2.1"):
    return f"wcag-{wcag_version}_rules"


def get_collection(wcag_version: WcagVersion = "2.1"):
    client = get_vector_client(CHROMADB_WCAG_PATH)
    embedding_function = get_embedding_model()
    collection_name = create_collection_name(wcag_version)
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"},
    )
    return collection
