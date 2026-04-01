"""
RAG Retriever — retrieves relevant chunks from ChromaDB.
"""
from rag.indexer import get_chroma_client, get_embedding_function, COLLECTION_NAME, index_documents


def retrieve_chunks(query: str, top_k: int = 5) -> list[dict]:
    """Retrieve top-k most relevant chunks for a query."""
    client = get_chroma_client()
    ef = get_embedding_function()

    # Ensure collection exists
    existing = client.list_collections()
    if not any(c.name == COLLECTION_NAME for c in existing):
        print("Knowledge base not indexed. Indexing now...")
        index_documents()

    collection = client.get_collection(name=COLLECTION_NAME, embedding_function=ef)

    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for doc, meta, dist in zip(documents, metadatas, distances):
        relevance_score = max(0.0, 1.0 - dist)  # cosine distance -> similarity
        chunks.append({
            "chunk_id": f"{meta['source_file']}_chunk_{meta['chunk_index']}",
            "document_title": meta["document_title"],
            "content": doc,
            "relevance_score": round(relevance_score, 4),
            "page_or_section": f"chunk {meta['chunk_index']}",
        })

    return chunks
