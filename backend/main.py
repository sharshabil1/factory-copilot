"""
main.py
-------
FastAPI entry point. Endpoints consumed by the Vue frontend store:

  POST /auth/login
  POST /chat
  GET  /documents
  POST /documents/upload
  GET  /inventory
  GET  /admin/logs
  GET  /admin/stats
"""

import os, io, time, asyncio
from contextlib import asynccontextmanager
from typing import List, Optional

import asyncpg
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from database import init_db
from services.ai_agent import run_agent
from services.rag_pipeline import store_chunks

DB_DSN = os.getenv(
    "DATABASE_URL_RAW",
    "postgresql://postgres:password@db:5432/factory_copilot",
)

# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="Factory Copilot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


# ── DB helper ─────────────────────────────────────────────────────────────────
async def db() -> asyncpg.Connection:
    conn = await asyncpg.connect(DB_DSN)
    try:
        yield conn
    finally:
        await conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/auth/login")
async def login(req: LoginRequest, conn: asyncpg.Connection = Depends(db)):
    row = await conn.fetchrow(
        "SELECT id, username, role, password_hash FROM users WHERE username = $1",
        req.username,
    )
    if not row:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Simple plaintext check for hackathon; swap for bcrypt in production
    if row["password_hash"] != req.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    import base64
    token = base64.b64encode(f"{row['id']}:{row['username']}".encode()).decode()

    return {
        "access_token": token,
        "token_type":   "bearer",
        "user_id":      row["id"],
        "username":     row["username"],
        "role":         row["role"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# CHAT
# ─────────────────────────────────────────────────────────────────────────────
class ChatMessage(BaseModel):
    role:    str   # "user" | "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []
    user_id: Optional[int] = None

class ChatResponse(BaseModel):
    answer:    str
    sources:   List[str] = []
    tool_used: str = "none"
    sql:       Optional[str] = None

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    history = [{"role": m.role, "content": m.content} for m in (req.history or [])]

    started = time.time()
    try:
        result = await run_agent(req.message, chat_history=history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    latency_ms = int((time.time() - started) * 1000)

    if req.user_id:
        asyncio.create_task(_log_usage(req.user_id, req.message, result["tool_used"], latency_ms))

    return ChatResponse(
        answer    = result["answer"],
        sources   = result["sources"],
        tool_used = result["tool_used"],
        sql       = result.get("sql"),
    )


async def _log_usage(user_id: int, query: str, tool: str, latency_ms: int):
    try:
        conn = await asyncpg.connect(DB_DSN)
        await conn.execute(
            "INSERT INTO usage_logs (user_id, query, tool_used, latency_ms) VALUES ($1,$2,$3,$4)",
            user_id, query, tool, latency_ms,
        )
        await conn.close()
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENTS
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/documents")
async def list_documents(conn: asyncpg.Connection = Depends(db)):
    rows = await conn.fetch(
        "SELECT id, filename, original_name, status, chunk_count, uploaded_at FROM documents ORDER BY uploaded_at DESC"
    )
    return [dict(r) for r in rows]


@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    conn: asyncpg.Connection = Depends(db),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    row = await conn.fetchrow(
        """
        INSERT INTO documents (filename, original_name, status)
        VALUES ($1, $2, 'processing')
        RETURNING id
        """,
        file.filename,
        file.filename,
    )
    doc_id = row["id"]

    content = await file.read()
    chunks  = _pdf_to_chunks(content)

    try:
        chunk_count = await store_chunks(doc_id, chunks)
        await conn.execute(
            "UPDATE documents SET status='ready', chunk_count=$1 WHERE id=$2",
            chunk_count, doc_id,
        )
        status = "ready"
    except Exception as e:
        await conn.execute("UPDATE documents SET status='failed' WHERE id=$1", doc_id)
        status = "failed"
        chunk_count = 0

    return {
        "id":            doc_id,
        "original_name": file.filename,
        "status":        status,
        "chunk_count":   chunk_count,
    }


def _pdf_to_chunks(pdf_bytes: bytes, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    try:
        import pypdf
        reader    = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        full_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        full_text = ""

    if not full_text.strip():
        return []

    words  = full_text.split()
    chunks = []
    start  = 0
    while start < len(words):
        chunk = " ".join(words[start : start + chunk_size])
        chunks.append(chunk)
        start += chunk_size - overlap

    return [c for c in chunks if c.strip()]


# ─────────────────────────────────────────────────────────────────────────────
# INVENTORY
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/inventory")
async def get_inventory(conn: asyncpg.Connection = Depends(db)):
    rows = await conn.fetch(
        """
        SELECT id, department_id, metric_period, total_revenue,
               operational_costs, incidents_reported, performance_score
        FROM odoo_department_metrics
        WHERE department_id = 'inventory'
        ORDER BY metric_period DESC
        """
    )
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/admin/logs")
async def admin_logs(limit: int = 50, conn: asyncpg.Connection = Depends(db)):
    rows = await conn.fetch(
        """
        SELECT id, user_id, query, tool_used, latency_ms, created_at
        FROM usage_logs
        ORDER BY created_at DESC
        LIMIT $1
        """,
        limit,
    )
    return [dict(r) for r in rows]


@app.get("/admin/stats")
async def admin_stats(conn: asyncpg.Connection = Depends(db)):
    row = await conn.fetchrow(
        """
        SELECT
            COUNT(*)                                                               AS total_queries,
            ROUND(AVG(latency_ms))                                                 AS avg_latency_ms,
            ROUND(100.0 * SUM(CASE WHEN tool_used='Search_Docs' THEN 1 ELSE 0 END)
                  / NULLIF(COUNT(*), 0))                                           AS rag_pct,
            COUNT(DISTINCT user_id)                                                AS active_users
        FROM usage_logs
        """
    )
    series = await conn.fetch(
        """
        SELECT
            DATE(created_at)                                                  AS day,
            SUM(CASE WHEN tool_used='Search_Docs' THEN 1 ELSE 0 END)          AS rag,
            SUM(CASE WHEN tool_used='Query_DB'    THEN 1 ELSE 0 END)          AS odoo
        FROM usage_logs
        WHERE created_at >= NOW() - INTERVAL '7 days'
        GROUP BY DATE(created_at)
        ORDER BY day
        """
    )
    return {
        "totalQueries": row["total_queries"]  or 0,
        "avgLatencyMs": row["avg_latency_ms"] or 0,
        "ragPct":       row["rag_pct"]        or 0,
        "activeUsers":  row["active_users"]   or 0,
        "dailySeries":  [dict(r) for r in series],
    }


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}