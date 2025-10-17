from typing import TypedDict, List
import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from .retriever import get_retriever, get_vectorstore
from .url_tools import extract_urls, ingest_url
from functools import lru_cache

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
RELEVANCE_THRESHOLD = float(os.getenv("RELEVANCE_THRESHOLD", "0.5"))

class ChatState(TypedDict):
    query: str
    urls: List[str]
    answer: str
    sources: List[str]
    used_rag: bool

# Cache LLM instance for reuse
@lru_cache(maxsize=1)
def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=GOOGLE_API_KEY,
        temperature=0.2,
    )

def classify_node(state: ChatState) -> ChatState:
    """Extract URLs from query."""
    urls = extract_urls(state["query"])
    state["urls"] = urls
    state["sources"] = []
    state["used_rag"] = False
    return state

def route_classify(state: ChatState) -> str:
    """Route based on URL presence."""
    if state.get("urls"):
        return "ingest"
    return "rag_query"

def ingest_node(state: ChatState) -> ChatState:
    """Ingest URLs with better error handling."""
    for url in state["urls"]:
        try:
            ingest_url(url)
            print(f"[INFO] Successfully ingested {url}")
        except Exception as e:
            print(f"[ERROR] Failed to ingest {url}: {str(e)}")
    return state

def rag_query_node(state: ChatState) -> ChatState:
    """
    RAG query with relevance checking.
    Falls back to general LLM if retrieved docs aren't relevant enough.
    """
    llm = get_llm()
    vectorstore = get_vectorstore()
    
    # Use similarity_search_with_score to get relevance scores
    try:
        docs_with_scores = vectorstore.similarity_search_with_score(
            state["query"], 
            k=5
        )
        
        print(f"[DEBUG] Retrieved {len(docs_with_scores)} docs with scores")
        
        # Filter by relevance threshold (lower score = more similar in most embeddings)
        # Note: Chroma uses distance, so lower is better
        relevant_docs = [(doc, score) for doc, score in docs_with_scores if score < RELEVANCE_THRESHOLD]
        
        if relevant_docs:
            print(f"[DEBUG] {len(relevant_docs)} docs passed relevance threshold ({RELEVANCE_THRESHOLD})")
            
            # Extract just the documents
            docs = [doc for doc, score in relevant_docs]
            
            # Custom prompt that emphasizes using context
            qa_prompt = PromptTemplate(
                template="""Use the following pieces of context to answer the question. 
If the context doesn't contain relevant information to answer the question, say "I don't have enough information in the provided context to answer that question."

Context:
{context}

Question: {question}

Answer:""",
                input_variables=["context", "question"]
            )
            
            # Use RAG with relevant context
            retriever = get_retriever()
            qa = RetrievalQA.from_chain_type(
                llm=llm,
                retriever=retriever,
                chain_type="stuff",
                return_source_documents=True,
                chain_type_kwargs={"prompt": qa_prompt}
            )
            
            res = qa({"query": state["query"]})
            answer = res["result"]
            
            # Check if the RAG system says it doesn't have info
            no_info_phrases = [
                "don't have enough information",
                "don't have information",
                "context doesn't contain",
                "not mentioned in",
                "cannot find",
                "no information"
            ]
            
            if any(phrase in answer.lower() for phrase in no_info_phrases):
                # RAG couldn't answer, fall back to general LLM
                print("[INFO] RAG couldn't answer, falling back to general LLM")
                prompt = f"Answer this question conversationally:\n\n{state['query']}"
                res = llm.invoke(prompt)
                state["answer"] = res.content
                state["used_rag"] = False
                state["sources"] = []
            else:
                # RAG provided a good answer
                state["answer"] = answer
                state["used_rag"] = True
                if "source_documents" in res:
                    sources = [doc.metadata.get("source", "unknown") for doc in res["source_documents"]]
                    state["sources"] = list(set(sources))
        else:
            # No relevant documents found, use general LLM
            print(f"[INFO] No docs passed relevance threshold, using general LLM")
            prompt = f"Answer this question conversationally:\n\n{state['query']}"
            res = llm.invoke(prompt)
            state["answer"] = res.content
            state["used_rag"] = False
            state["sources"] = []
            
    except Exception as e:
        # If similarity search fails, fall back to general LLM
        print(f"[WARN] Error in similarity search: {e}, falling back to general LLM")
        prompt = f"Answer this question conversationally:\n\n{state['query']}"
        res = llm.invoke(prompt)
        state["answer"] = res.content
        state["used_rag"] = False
        state["sources"] = []

    return state

# Build graph once and cache it
@lru_cache(maxsize=1)
def build_graph():
    """Build and cache the LangGraph workflow."""
    g = StateGraph(ChatState)

    g.add_node("classify", classify_node)
    g.add_node("ingest", ingest_node)
    g.add_node("rag_query", rag_query_node)

    g.set_entry_point("classify")

    g.add_conditional_edges(
        "classify",
        route_classify,   
        {
            "ingest": "ingest",
            "rag_query": "rag_query",
        },
    )

    g.add_edge("ingest", "rag_query")
    g.set_finish_point("rag_query")

    return g.compile()

def run_chat(query: str):
    """Execute chat with cached graph."""
    graph = build_graph()
    initial: ChatState = {
        "query": query, 
        "urls": [], 
        "answer": "",
        "sources": [],
        "used_rag": False
    }
    result = graph.invoke(initial)
    return result