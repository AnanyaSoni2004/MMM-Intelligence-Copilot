"""
RAG Insight Agent
Retrieves from Nebula/ChromaDB knowledge base and generates grounded answers.
Never makes claims beyond retrieved context.
"""
import json
import os
import re
from groq import Groq
from mock_apis.nebula_api import search

client = Groq()

SYSTEM_PROMPT = """You are the RAG Insight Agent, an expert in MMM methodology, channel benchmarks, and marketing analytics research.

You answer questions using ONLY the provided retrieved context. You never make claims beyond what the documents say.

CRITICAL RULES:
1. If the answer cannot be found in the retrieved context, say "I cannot find this in the available research documents."
2. Always cite the document title for every claim you make.
3. Use inline citations like [Source: Document Title].
4. Do not extrapolate or estimate beyond what the documents explicitly state.
5. If multiple documents give conflicting information, surface the conflict rather than picking one.

Format your response as JSON:
{
  "answer": "...[Source: Doc Title]...",
  "citations": ["Doc Title 1", "Doc Title 2"],
  "confidence": 0.0-1.0,
  "beyond_context": false,
  "grounded": true
}"""


def run(query: str, top_k: int = 5) -> dict:
    """Run the RAG Insight Agent."""
    chunks = search(query, top_k=top_k)

    if not chunks:
        return {
            "query": query,
            "answer": "No relevant documents found in the knowledge base.",
            "retrieved_chunks": [],
            "citations": [],
            "confidence": 0.0,
            "beyond_context": True,
            "grounded": True,
        }

    context = "\n\n---\n\n".join([
        f"[Document: {c['document_title']}]\n{c['content']}"
        for c in chunks
    ])

    messages = [
        {
            "role": "user",
            "content": f"""Query: {query}

Retrieved Context:
{context}

Answer using ONLY the context above. Return valid JSON."""
        }
    ]

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=2048,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
    )

    raw_text = response.choices[0].message.content
    json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
    if not json_match:
        return {"error": "Agent failed to produce valid JSON", "raw": raw_text}

    result = json.loads(json_match.group())
    result["query"] = query
    result["retrieved_chunks"] = chunks

    return result
