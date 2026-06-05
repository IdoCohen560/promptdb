"""FastAPI app — a secondary interface over the agent core. Serves the streaming web demo.

Cost protection for a public LLM endpoint: optional API key + per-IP rate limit + request-id logging.
"""

import json
import logging
import os
import time
import uuid
from collections import defaultdict, deque
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from promptdb.agent.graph import build_graph
from promptdb.agent.providers import DEFAULT_PROVIDER, make_llm, model_for
from promptdb.api.limits import check_demo_allowed, demo_status, record_demo_usage

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("promptdb")

API_KEY = os.environ.get("PROMPTDB_API_KEY", "")          # if set, required on /query*
RATE_LIMIT = int(os.environ.get("PROMPTDB_RATE_LIMIT", "20"))  # requests per window per IP
RATE_WINDOW = 60.0
WEB = Path(__file__).resolve().parents[3] / "web"

app = FastAPI(title="PromptDB")
_hits: dict[str, deque] = defaultdict(deque)


class Query(BaseModel):
    question: str
    provider: str | None = None   # BYO: "anthropic" | "openai" | "ollama"; None = demo (server key)
    model: str | None = None
    api_key: str | None = None    # BYO key — encapsulated in the model client, never stored


def _run_config(q: "Query") -> dict | None:
    """Build a LangGraph config for a BYO-key request, or None for the demo path."""
    if not q.provider:
        return None
    llm = make_llm(q.provider, q.model, q.api_key)
    return {"configurable": {"llm": llm, "model_name": model_for(q.provider, q.model)}}


def _check_key(key: str | None) -> None:
    if API_KEY and key != API_KEY:
        raise HTTPException(status_code=401, detail="invalid or missing API key")


def _check_rate(ip: str) -> None:
    now = time.monotonic()
    dq = _hits[ip]
    while dq and now - dq[0] > RATE_WINDOW:
        dq.popleft()
    if len(dq) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="rate limit exceeded")
    dq.append(now)


@app.middleware("http")
async def request_id(request: Request, call_next):
    rid = uuid.uuid4().hex[:8]
    t0 = time.monotonic()
    response = await call_next(request)
    log.info("rid=%s %s %s %s %dms", rid, request.method, request.url.path,
             response.status_code, int(1000 * (time.monotonic() - t0)))
    response.headers["X-Request-ID"] = rid
    return response


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/usage")
def usage(request: Request) -> dict:
    """Remaining free demo quota for this IP — lets the UI show '3 of 5 free queries left'."""
    return demo_status(request.client.host)


@app.post("/query")
def query(q: Query, request: Request, x_api_key: str | None = Header(None)) -> dict:
    _check_key(x_api_key)
    ip = request.client.host
    _check_rate(ip)
    byo = bool(q.provider)
    if not byo:  # demo path runs on the server key — enforce free-query + daily-budget caps
        ok, msg = check_demo_allowed(ip)
        if not ok:
            raise HTTPException(status_code=402, detail=msg)
    t0 = time.monotonic()
    result = build_graph().invoke({"question": q.question}, config=_run_config(q))
    cost = result.get("cost_usd", 0.0)
    if not byo:
        record_demo_usage(ip, cost)
    return {
        "question": q.question, "sql": result.get("sql"), "columns": result.get("columns"),
        "rows": result.get("rows"), "answer": result.get("answer"), "error": result.get("error"),
        "cost_usd": cost, "latency_s": round(time.monotonic() - t0, 2),
        "usage": None if byo else demo_status(ip),
    }


@app.get("/query/stream")
def query_stream(q: str, request: Request, key: str | None = None,
                 x_api_key: str | None = Header(None)) -> StreamingResponse:
    _check_key(x_api_key or key)  # EventSource can't set headers, so allow ?key=
    ip = request.client.host
    _check_rate(ip)
    ok, msg = check_demo_allowed(ip)  # streaming demo runs on the server key
    if not ok:
        raise HTTPException(status_code=402, detail=msg)

    def gen():
        final_cost = 0.0
        for chunk in build_graph().stream({"question": q}, stream_mode="updates"):
            for node, update in chunk.items():
                payload = {"node": node}
                for field in ("sql", "answer", "error", "columns", "rows", "cost_usd"):
                    if update.get(field) is not None:
                        payload[field] = update[field]
                        if field == "cost_usd":
                            final_cost = update[field]
                yield f"data: {json.dumps(payload, default=str)}\n\n"
        record_demo_usage(ip, final_cost)
        yield f"data: {json.dumps({'node': 'done', 'usage': demo_status(ip)})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB / "index.html")
