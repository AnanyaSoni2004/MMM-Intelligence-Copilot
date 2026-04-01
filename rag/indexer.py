"""
RAG Indexer — chunks documents and loads them into ChromaDB.
"""
import os
import uuid
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path

COLLECTION_NAME = "mmm_knowledge_base"
SAMPLE_DOCS_DIR = Path(__file__).parent / "sample_docs"
CHROMA_PATH = Path(__file__).parent.parent / ".chroma_db"


def get_chroma_client():
    return chromadb.PersistentClient(path=str(CHROMA_PATH))


def get_embedding_function():
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 80) -> list[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def index_documents(force_reindex: bool = False):
    """Index all sample documents into ChromaDB."""
    client = get_chroma_client()
    ef = get_embedding_function()

    # Check if already indexed
    existing = client.list_collections()
    if any(c.name == COLLECTION_NAME for c in existing) and not force_reindex:
        print(f"Collection '{COLLECTION_NAME}' already exists. Skipping indexing.")
        return

    if any(c.name == COLLECTION_NAME for c in existing):
        client.delete_collection(COLLECTION_NAME)

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    doc_files = list(SAMPLE_DOCS_DIR.glob("*.txt"))
    total_chunks = 0

    for doc_file in doc_files:
        text = doc_file.read_text(encoding="utf-8")
        chunks = chunk_text(text)

        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [
            {
                "document_title": doc_file.stem.replace("_", " ").title(),
                "source_file": doc_file.name,
                "chunk_index": i,
            }
            for i in range(len(chunks))
        ]

        collection.add(documents=chunks, ids=ids, metadatas=metadatas)
        total_chunks += len(chunks)
        print(f"  Indexed {doc_file.name}: {len(chunks)} chunks")

    print(f"Indexing complete. Total chunks: {total_chunks}")


if __name__ == "__main__":
    print("Indexing MMM knowledge base...")
    index_documents(force_reindex=True)
