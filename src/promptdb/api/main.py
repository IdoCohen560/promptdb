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
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from urllib.parse import urlparse

from sqlalchemy import create_engine

from promptdb.agent.graph import build_graph
from promptdb.agent.providers import PRESETS, list_models, make_llm, model_for
from promptdb.api.limits import check_demo_allowed, demo_status, record_demo_usage
from promptdb.api.remote_db import (
    DatabaseUnreachable,
    UnsafeDatabaseURL,
    _assert_public_host,
    safe_engine,
)
from promptdb.api.sample_seed import (
    denied_tables,
    deny_columns,
    sample_tables,
    sample_url,
    star_guard_tables,
)
from promptdb.data.schema_graph import schema_json


def _guard_base_url(base_url: str) -> None:
    """SSRF guard for a model endpoint: its host must resolve to a public address."""
    _assert_public_host(urlparse(base_url).hostname)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("promptdb")

API_KEY = os.environ.get("PROMPTDB_API_KEY", "")          # if set, required on /query*
RATE_LIMIT = int(os.environ.get("PROMPTDB_RATE_LIMIT", "20"))  # requests per window per IP
RATE_WINDOW = 60.0
WEB = Path(__file__).resolve().parents[3] / "web"

app = FastAPI(title="PromptDB")

# The Vercel UI is served from a different origin; allow it (default open for the public demo).
_origins = os.environ.get("PROMPTDB_CORS_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins.split(",")] if _origins != "*" else ["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
_hits: dict[str, deque] = defaultdict(deque)


class Query(BaseModel):
    question: str
    provider: str | None = None   # "anthropic" (native) or a preset name; None = demo (server key)
    model: str | None = None
    api_key: str | None = None    # BYO key — encapsulated in the model client, never stored
    base_url: str | None = None   # any OpenAI-compatible endpoint (OpenRouter, OpenAI, custom)
    database_url: str | None = None  # connect your own cloud DB (read-only); None = demo Chinook
    sample: bool = False          # query the built-in sample bookshop DB (server-side)


class ConnectRequest(BaseModel):
    database_url: str


class ModelsRequest(BaseModel):
    provider: str | None = None
    base_url: str | None = None
    api_key: str | None = None


def _effective_base(provider: str | None, base_url: str | None) -> str | None:
    return base_url or PRESETS.get((provider or "").lower())


def _run_config(q: "Query") -> dict | None:
    """Build a LangGraph config: a BYO model and/or a connected database. None for the pure demo."""
    cfg: dict = {}
    if q.provider or q.base_url:
        base = _effective_base(q.provider, q.base_url)
        if base:
            _guard_base_url(base)  # SSRF: a custom/local model host must be public
        cfg["llm"] = make_llm(q.provider, q.model, q.api_key, q.base_url)
        cfg["model_name"] = model_for(q.provider, q.model)
    if q.database_url:
        cfg["engine"] = safe_engine(q.database_url)  # raises UnsafeDatabaseURL on a bad host
    elif q.sample and sample_url():
        cfg["engine"] = create_engine(sample_url(), connect_args={"connect_timeout": 10})
        cfg["denied_tables"] = denied_tables()       # optional whole-table block (off → show all)
        cfg["deny_columns"] = deny_columns()         # credential columns (e.g. password_hash)
        cfg["star_tables"] = star_guard_tables()     # tables where SELECT * is blocked
    return {"configurable": cfg} if cfg else None


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


def _identity(request: Request, client_id: str | None) -> str:
    """Who to meter the demo against: a per-browser client id when present, else the IP.
    Lets distinct users behind one shared IP each get their own free quota."""
    return (client_id or "").strip() or request.client.host


@app.get("/usage")
def usage(request: Request, x_client_id: str | None = Header(None)) -> dict:
    """Remaining free demo quota for this user — lets the UI show '3 of 5 free queries left'."""
    return demo_status(_identity(request, x_client_id))


@app.get("/schema")
def schema() -> dict:
    """Structured schema of the active database for the UI's ER blueprint."""
    return schema_json()


@app.get("/sample")
def sample() -> dict:
    """A ready-to-use sample database (a synthetic bookshop) so visitors can try the connect flow
    without their own DB. Server-side only (free-tier DB is internal-network only); returns schema."""
    try:
        url = sample_url()  # seeds on first call (server-side, idempotent)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"sample database unavailable: {exc}")
    if not url:
        raise HTTPException(status_code=404, detail="no sample database configured")
    try:
        allow = sample_tables()
        eng = create_engine(url, connect_args={"connect_timeout": 10})
        return {"schema": schema_json(eng, only=set(allow) if allow else None)}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"sample database unavailable: {exc}")


@app.post("/models")
def models(req: ModelsRequest, request: Request) -> dict:
    """List models from an OpenAI-compatible endpoint (OpenRouter, OpenAI, custom). SSRF-guarded."""
    _check_rate(request.client.host)
    base = _effective_base(req.provider, req.base_url)
    if not base:
        raise HTTPException(status_code=400, detail="no base_url or known provider")
    try:
        _guard_base_url(base)
        return {"models": list_models(base, req.api_key)}
    except UnsafeDatabaseURL as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # noqa: BLE001 — surface listing failures to the UI
        raise HTTPException(status_code=502, detail=f"could not list models: {exc}")


@app.post("/connect")
def connect(req: ConnectRequest, request: Request) -> dict:
    """Validate a user connection string and return its schema, so the UI can render the ER
    blueprint and confirm connectivity before any query runs. SSRF-guarded; read-only intent."""
    _check_rate(request.client.host)
    try:
        eng = safe_engine(req.database_url)
        return {"ok": True, "schema": schema_json(eng)}
    except UnsafeDatabaseURL as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # noqa: BLE001 — surface connection failures to the UI
        raise HTTPException(status_code=502, detail=f"could not connect: {exc}")


@app.post("/query")
def query(q: Query, request: Request, x_api_key: str | None = Header(None),
          x_client_id: str | None = Header(None)) -> dict:
    _check_key(x_api_key)
    _check_rate(request.client.host)               # per-IP burst limit
    who = _identity(request, x_client_id)           # per-user demo quota
    byo = bool(q.provider or q.base_url)  # any BYO model (preset or custom endpoint) bypasses the cap
    if not byo:  # demo path runs on the server key — enforce free-query + daily-budget caps
        ok, msg = check_demo_allowed(who)
        if not ok:
            raise HTTPException(status_code=402, detail=msg)
    try:
        config = _run_config(q)
    except UnsafeDatabaseURL as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except DatabaseUnreachable as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    t0 = time.monotonic()
    result = build_graph().invoke({"question": q.question}, config=config)
    cost = result.get("cost_usd", 0.0)
    if not byo:
        record_demo_usage(who, cost)
    return {
        "question": q.question, "sql": result.get("sql"), "columns": result.get("columns"),
        "rows": result.get("rows"), "answer": result.get("answer"), "error": result.get("error"),
        "cost_usd": cost, "latency_s": round(time.monotonic() - t0, 2),
        "usage": None if byo else demo_status(who),
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
