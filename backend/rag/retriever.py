import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from .embeddings import get_embeddings
from functools import lru_cache

load_dotenv()

PERSIST_DIR = os.getenv("PERSIST_DIR", "data/chroma_db")

# Singleton pattern for vector store
_vectorstore_instance = None

def get_vectorstore():
    """Get or create the Chroma vector database singleton."""
    global _vectorstore_instance
    
    if _vectorstore_instance is None:
        os.makedirs(PERSIST_DIR, exist_ok=True)
        _vectorstore_instance = Chroma(
            persist_directory=PERSIST_DIR,
            embedding_function=get_embeddings()
        )
    
    return _vectorstore_instance

def get_retriever(k: int = 5):
    """
    Return a retriever with configurable top-k results.
    Uses the singleton vectorstore instance.
    """
    return get_vectorstore().as_retriever(
        search_kwargs={"k": k}
    )

def reset_vectorstore():
    """Reset the singleton (useful for testing or reloading)."""
    global _vectorstore_instance
    _vectorstore_instance = None