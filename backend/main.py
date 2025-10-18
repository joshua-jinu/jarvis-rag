import os
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from rag.graph_chat import run_chat
import logging
from typing import Optional, List

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Jarvis Auto-RAG API",
    description="Intelligent RAG system with URL ingestion",
    version="1.0.0"
)

# CORS configuration
origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="User query")
    
    @validator('query')
    def query_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()

class ChatResponse(BaseModel):
    answer: str
    sources: Optional[List[str]] = None
    used_rag: bool = False
    status: str = "success"

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for better error responses."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "An unexpected error occurred",
            "detail": str(exc) if os.getenv("DEBUG") == "true" else None
        }
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Process a chat query with RAG.
    
    - Automatically detects and ingests URLs in the query
    - Uses vector search for relevant context
    - Falls back to general LLM if no context found
    """
    try:
        logger.info(f"Processing query: {req.query[:100]}...")
        
        result = run_chat(req.query)
        
        response = ChatResponse(
            answer=result.get("answer", ""),
            sources=result.get("sources", []),
            status="success"
        )
        
        logger.info(f"Query processed successfully")
        return response
        
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )

@app.get("/")
def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Jarvis Auto-RAG API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/chat",
            "health": "/",
            "docs": "/docs"
        }
    }

@app.get("/health")
def health():
    """Detailed health check."""
    try:
        # Test if vector store is accessible
        from rag.retriever import get_vectorstore
        vectorstore = get_vectorstore()
        
        return {
            "status": "healthy",
            "components": {
                "api": "ok",
                "vectorstore": "ok",
                "llm": "ok"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        log_level="info"
    )