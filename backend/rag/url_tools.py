import re
import requests
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from .retriever import get_vectorstore
from urllib.parse import urlparse
from typing import List
import hashlib

URL_PATTERN = re.compile(r"https?://\S+")

# Cache ingested URLs to avoid re-processing
_ingested_urls = set()

def extract_urls(text: str) -> List[str]:
    """Extract and validate URLs from text."""
    urls = URL_PATTERN.findall(text)
    validated = []
    
    for url in urls:
        try:
            parsed = urlparse(url)
            if parsed.scheme in ['http', 'https'] and parsed.netloc:
                validated.append(url)
        except Exception:
            continue
    
    return validated

def extract_text_from_html(html: str) -> str:
    """Extract clean text from HTML."""
    soup = BeautifulSoup(html, "lxml")
    
    # Remove unwanted elements
    for tag in soup(["script", "style", "noscript", "iframe", "nav", "footer", "header"]):
        tag.decompose()
    
    # Get text with better formatting
    text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    return "\n\n".join(lines)

def get_url_hash(url: str) -> str:
    """Generate a hash for URL to track ingestion."""
    return hashlib.md5(url.encode()).hexdigest()

def ingest_url(url: str, force: bool = False) -> List[Document]:
    """
    Fetch and embed content from URL.
    
    Args:
        url: The URL to ingest
        force: If True, re-ingest even if already processed
    
    Returns:
        List of Document objects created
    """
    url_hash = get_url_hash(url)
    
    # Skip if already ingested (unless forced)
    if not force and url_hash in _ingested_urls:
        print(f"[INFO] URL already ingested: {url}")
        return []
    
    try:
        # Fetch with better headers and timeout
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Jarvis-RAG/1.0)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        
        # Extract text
        html = resp.text
        text = extract_text_from_html(html)
        
        # Validate content length
        if len(text) < 50:
            raise ValueError(f"Insufficient content: only {len(text)} characters")
        
        # Split into chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = splitter.split_text(text)
        
        # Create documents with metadata
        docs = [
            Document(
                page_content=chunk,
                metadata={
                    "source": url,
                    "url_hash": url_hash,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            )
            for i, chunk in enumerate(chunks)
        ]
        
        # Add to vector store
        vectordb = get_vectorstore()
        vectordb.add_documents(docs)
        vectordb.persist()
        
        # Mark as ingested
        _ingested_urls.add(url_hash)
        
        print(f"[INFO] Ingested {len(docs)} chunks from {url}")
        return docs
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch URL: {str(e)}")
    except Exception as e:
        raise Exception(f"Error processing URL: {str(e)}")

def clear_ingestion_cache():
    """Clear the ingested URLs cache."""
    global _ingested_urls
    _ingested_urls.clear()