from langchain_community.embeddings import HuggingFaceEmbeddings
from functools import lru_cache

@lru_cache(maxsize=1)
def get_embeddings():
    """
    Get cached embeddings model.
    Loading the model once improves performance significantly.
    """
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},  # Change to 'cuda' if GPU available
        encode_kwargs={'normalize_embeddings': True}
    )