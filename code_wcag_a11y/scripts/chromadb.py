import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from code_wcag_a11y.globals import CHROMADB_WCAG_PATH, COLLECTION_NAME


def get_vector_client(path: str):
    return chromadb.PersistentClient(path=path)


def get_embedding_model():
    return SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")


client = get_vector_client(CHROMADB_WCAG_PATH)
embedding_function = get_embedding_model()

collection = client.get_or_create_collection(
    name=COLLECTION_NAME, embedding_function=embedding_function
)
