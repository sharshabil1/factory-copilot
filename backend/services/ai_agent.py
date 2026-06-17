"""
ai_agent.py
-----------
LangChain agent that routes user messages to one of two tools:

  • Search_Docs  → RAG pipeline (semantic search over uploaded manuals)
  • Query_DB     → Text-to-SQL against odoo_department_metrics
                   (scoped to accounting & inventory departments)

Model: Gemini 1.5 Flash via langchain-google-genai
"""

import os
import json
import asyncio
import asyncpg
from typing import Any, Dict, List

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain.tools import tool
from langchain_core.messages import HumanMessage, AIMessage

from services.rag_pipeline import search_docs

# ── Config ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DB_DSN = os.getenv(
    "DATABASE_URL_RAW",
    "postgresql://postgres:password@localhost:5432/factory_copilot"
)

# ── DB helper ─────────────────────────────────────────────────────────────────
async def _run_sql(query: str, params: tuple = ()) -> List[Dict]:
    conn = await asyncpg.connect(DB_DSN)
    try:
        rows = await conn.fetch(query, *params)
        return [dict(r) for r in rows]
    finally:
        await conn.close()


# ── Tool 1: Search_Docs (RAG) ─────────────────────────────────────────────────
@tool
async def Search_Docs(query: str) -> str:
    """
    Search uploaded company documents (manuals, SOPs, policies) for information
    relevant to the user's question.
    Use this when the user asks about procedures, safety, specifications, or
    anything that would be found in a document or manual.
    Returns the most relevant text passages and their source filenames.
    """
    results = await search_docs(query, top_k=5)

    if not results:
        return json.dumps({
            "answer": "No relevant documents found.",
            "sources": []
        })

    # Build a readable context block
    context_parts = []
    sources = []
    seen_files = set()

    for r in results:
        if r["similarity"] < 0.3:   # skip low-confidence matches
            continue
        context_parts.append(
            f"[Source: {r['filename']} | chunk {r['chunk_index']}]\n{r['chunk_text']}"
        )
        if r["filename"] not in seen_files:
            sources.append(r["filename"])
            seen_files.add(r["filename"])

    if not context_parts:
        return json.dumps({
            "answer": "No sufficiently relevant document sections found.",
            "sources": []
        })

    context = "\n\n---\n\n".join(context_parts)
    return json.dumps({
        "context": context,
        "sources": sources
    })


# ── Tool 2: Query_DB (Text → SQL against odoo_department_metrics) ─────────────

# Exposed schema description so the LLM knows what columns exist
_SCHEMA_DESCRIPTION = """
Table: odoo_department_metrics
Columns:
  - id                  SERIAL PRIMARY KEY
  - department_id       VARCHAR   -- e.g. 'accounting', 'inventory'
  - metric_period       VARCHAR   -- e.g. '2024-Q1', '2024-06'
  - total_revenue       NUMERIC   -- total revenue for the period
  - operational_costs   NUMERIC   -- operational costs for the period
  - incidents_reported  INTEGER   -- number of incidents reported
  - performance_score   DECIMAL   -- 0.00 to 1.00 performance score

Allowed departments (use exactly): 'accounting', 'inventory'
"""

@tool
async def Query_DB(natural_language_request: str) -> str:
    """
    Query the factory database for metrics about the Accounting or Inventory departments.
    Use this when the user asks about revenue, costs, performance scores, incidents,
    or any numerical/operational data for these two departments.
    Input should be the user's question in natural language.
    """
    # Step 1: Ask Gemini to generate safe SQL from the NL request
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=GEMINI_API_KEY,
        temperature=0,
    )

    sql_prompt = f"""You are a SQL expert. Given this schema:

{_SCHEMA_DESCRIPTION}

Generate a single, safe, read-only PostgreSQL SELECT query to answer:
"{natural_language_request}"

Rules:
- Only use the odoo_department_metrics table.
- Only SELECT, never INSERT/UPDATE/DELETE/DROP.
- Only filter on department_id values 'accounting' or 'inventory'.
- If the question is about both departments, don't filter by department_id.
- Return ONLY the raw SQL query, no explanation, no markdown fences.
"""

    loop = asyncio.get_event_loop()
    sql_response = await loop.run_in_executor(
        None,
        lambda: llm.invoke(sql_prompt).content.strip()
    )

    # Safety guard: reject any non-SELECT statement
    first_word = sql_response.strip().upper().split()[0] if sql_response.strip() else ""
    if first_word != "SELECT":
        return json.dumps({
            "error": "Generated query was not a SELECT statement. Refusing to execute.",
            "generated_sql": sql_response
        })

    # Step 2: Run the query
    try:
        rows = await _run_sql(sql_response)
    except Exception as e:
        return json.dumps({
            "error": f"Database error: {str(e)}",
            "generated_sql": sql_response
        })

    return json.dumps({
        "rows": rows,
        "generated_sql": sql_response,
        "row_count": len(rows)
    })


# ── Agent setup ───────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are Factory Copilot, an intelligent assistant for a manufacturing company.
You help managers and technicians in the **Accounting** and **Inventory** departments.

You have access to two tools:
1. **Search_Docs** — searches uploaded company documents and manuals.
2. **Query_DB** — queries live department metrics (revenue, costs, performance, incidents).

Decision rules:
- If the question is about numbers, KPIs, costs, revenue, performance, or incidents → use Query_DB.
- If the question is about procedures, safety, policies, specs, or "how to" → use Search_Docs.
- If unsure, try Query_DB first, then Search_Docs.
- If the database returns data, summarize it clearly in plain language.
- Always be concise and professional.
- When you use Search_Docs, mention the source document names in your answer.
- When you use Query_DB, briefly describe what data you retrieved.
"""

def _build_agent() -> Any:
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=GEMINI_API_KEY,
        temperature=0.2,
    )

    tools = [Search_Docs, Query_DB]

    return create_react_agent(llm, tools=tools, state_modifier=_SYSTEM_PROMPT)


# Lazy singleton so we build the agent once per process
_agent_executor: Any = None

def get_agent() -> Any:
    global _agent_executor
    if _agent_executor is None:
        _agent_executor = _build_agent()
    return _agent_executor


# ── Public entry point ────────────────────────────────────────────────────────

async def run_agent(
    user_message: str,
    chat_history: List[Dict[str, str]] | None = None,
) -> Dict[str, Any]:
    """
    Run the agent and return a structured response dict:
    {
        "answer":  str,          # final text answer for the user
        "sources": list[str],    # filenames if RAG was used, else []
        "tool_used": str,        # "Search_Docs" | "Query_DB" | "none"
        "sql": str | None,       # SQL if Query_DB was used
    }
    """
    agent = get_agent()

    # Convert simple history dicts to LangChain message format
    lc_history = []
    if chat_history:
        for msg in chat_history:
            if msg["role"] == "user":
                lc_history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_history.append(AIMessage(content=msg["content"]))

    # Append current user prompt
    lc_history.append(HumanMessage(content=user_message))

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: agent.invoke({
            "messages": lc_history,
        })
    )

    # LangGraph result contains a 'messages' array. The last item is the AI's final answer.
    messages = result.get("messages", [])
    raw_output = messages[-1].content if messages else ""

    # Parse sources / SQL from the intermediate tool messages
    sources: List[str] = []
    sql: str | None = None
    tool_used = "none"

    for msg in messages:
        if msg.type == "tool":
            if msg.name == "Search_Docs":
                tool_used = "Search_Docs"
                try:
                    obs_data = json.loads(msg.content)
                    sources = obs_data.get("sources", [])
                except (json.JSONDecodeError, AttributeError):
                    pass

            elif msg.name == "Query_DB":
                tool_used = "Query_DB"
                try:
                    obs_data = json.loads(msg.content)
                    sql = obs_data.get("generated_sql")
                except (json.JSONDecodeError, AttributeError):
                    pass

    return {
        "answer": raw_output,
        "sources": sources,
        "tool_used": tool_used,
        "sql": sql,
    }