"""
rag_pipeline.py
---------------
Handles:
  1. Embedding generation via Google Gemini (text-embedding-004, 1536-dim)
  2. Storing document chunks + embeddings into document_chunks table
  3. Semantic search: given a query string, return top-k relevant chunks
"""

import os
import asyncio
from typing import List, Dict, Any

import asyncpg
import google.generativeai as genai

# ── Gemini setup ─────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
genai.configure(api_key=GEMINI_API_KEY)

# Gemini embedding model — outputs 768 dims by default, but we request 1536
# via task_type so the vector matches our VECTOR(1536) column.
EMBEDDING_MODEL = "models/text-embedding-004"
EMBED_DIM = 1536  # must match CREATE TABLE document_chunks embedding VECTOR(1536)

# ── DB helper (raw asyncpg for speed) ────────────────────────────────────────
DB_DSN = os.getenv(
    "DATABASE_URL_RAW",
    "postgresql://postgres:password@localhost:5432/factory_copilot"
)


async def _get_conn() -> asyncpg.Connection:
    return await asyncpg.connect(DB_DSN)


# ── Embedding ────────────────────────────────────────────────────────────────

async def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Call Gemini embedding API for a list of strings.
    Returns a list of float vectors (one per input text).
    Note: Gemini text-embedding-004 natively outputs 768 dims.
          We pad/truncate to EMBED_DIM so it matches our column.
          For production swap to a 1536-dim model or resize the column.
    """
    loop = asyncio.get_event_loop()

    def _embed_sync(texts_batch):
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=texts_batch,
            task_type="retrieval_document",
        )
        return result["embedding"] if isinstance(texts_batch, str) else result["embedding"]

    # Run in executor so we don't block the async loop
    raw = await loop.run_in_executor(None, _embed_sync, texts if len(texts) > 1 else texts[0])

    # Normalise output shape: always list[list[float]]
    if isinstance(raw[0], float):
        raw = [raw]  # single string was passed

    # Pad or truncate to EMBED_DIM
    vectors = []
    for vec in raw:
        if len(vec) < EMBED_DIM:
            vec = vec + [0.0] * (EMBED_DIM - len(vec))
        else:
            vec = vec[:EMBED_DIM]
        vectors.append(vec)
    return vectors


async def embed_query(query: str) -> List[float]:
    """Embed a single query string for retrieval."""
    loop = asyncio.get_event_loop()

    def _embed_sync():
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=query,
            task_type="retrieval_query",
        )
        return result["embedding"]

    vec = await loop.run_in_executor(None, _embed_sync)
    if len(vec) < EMBED_DIM:
        vec = vec + [0.0] * (EMBED_DIM - len(vec))
    else:
        vec = vec[:EMBED_DIM]
    return vec


# ── Store chunks ─────────────────────────────────────────────────────────────

async def store_chunks(document_id: int, chunks: List[str]) -> int:
    """
    Embed `chunks` with Gemini and INSERT into document_chunks.
    Returns the number of chunks stored.
    """
    if not chunks:
        return 0

    vectors = await embed_texts(chunks)

    conn = await _get_conn()
    try:
        rows = [
            (document_id, idx, text, f"[{','.join(str(v) for v in vec)}]")
            for idx, (text, vec) in enumerate(zip(chunks, vectors))
        ]
        await conn.executemany(
            """
            INSERT INTO document_chunks (document_id, chunk_index, chunk_text, embedding)
            VALUES ($1, $2, $3, $4::vector)
            """,
            rows,
        )
    finally:
        await conn.close()

    return len(chunks)


# ── Semantic search ───────────────────────────────────────────────────────────

async def search_docs(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Embed `query`, then find the top_k most similar chunks via cosine distance.
    Returns list of dicts: {chunk_text, document_id, chunk_index, similarity, filename}
    """
    q_vec = await embed_query(query)
    vec_str = f"[{','.join(str(v) for v in q_vec)}]"

    conn = await _get_conn()
    try:
        rows = await conn.fetch(
            """
            SELECT
                dc.chunk_text,
                dc.document_id,
                dc.chunk_index,
                d.original_name  AS filename,
                1 - (dc.embedding <=> $1::vector) AS similarity
            FROM document_chunks dc
            JOIN documents d ON d.id = dc.document_id
            WHERE d.status = 'ready'
            ORDER BY dc.embedding <=> $1::vector
            LIMIT $2
            """,
            vec_str,
            top_k,
        )
    finally:
        await conn.close()

    return [
        {
            "chunk_text": r["chunk_text"],
            "document_id": r["document_id"],
            "chunk_index": r["chunk_index"],
            "filename": r["filename"],
            "similarity": float(r["similarity"]),
        }
        for r in rows
    ]