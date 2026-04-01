"""
Mock Aryma Nebula API
In production this would be replaced by actual Nebula API calls.
Here we delegate to our local ChromaDB RAG pipeline.
"""
from rag.retriever import retrieve_chunks

def search(query: str, top_k: int = 5) -> list[dict]:
    """Search the Nebula knowledge base."""
    return retrieve_chunks(query, top_k=top_k)
