"""
FastAPI application: the AG-UI endpoint plus a thin REST passthrough.

* ``POST /agent``   — AG-UI protocol endpoint. Body is a ``RunAgentInput``
  (AG-UI JSON), response is a ``text/event-stream`` of AG-UI events. This is what
  the React client (``@ag-ui/client`` HttpAgent) talks to.
* ``GET  /api/*``   — read-only JSON passthrough over the same tool dispatcher,
  for the deterministic Explorer UI (browse articles, tiers, checklists, ...)
  without spending a model call.
* ``GET  /health``  — liveness + provider/vector-store status.

Run locally::

    uv run uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from . import agent as agent_mod
from . import agui, settings as settings_mod, tools
from .llm import OpenAICompatibleTransport

app = FastAPI(
    title="EU AI Act — AG-UI server",
    version="1.0.0",
    description=(
        "AG-UI protocol server exposing the EU AI Act tool (full EUR-Lex text, "
        "curated analytical dataset, and RAG over the Act) to web frontends."
    ),
)

_origins = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001",
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins if o.strip()],
    # Dev convenience: any loopback port, so `next dev` picking 3001/3002 still works.
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health & meta
# ---------------------------------------------------------------------------
@app.get("/health")
def health() -> Dict[str, Any]:
    transport = OpenAICompatibleTransport()
    vs: Dict[str, Any] = {"status": "unknown"}
    try:
        from eu_ai_act import vector_store

        vs = vector_store.status()
    except Exception as exc:  # noqa: BLE001
        vs = {"status": "unavailable", "error": str(exc)}
    return {
        "status": "ok",
        "provider": {
            "base_url": transport.base_url,
            "model": transport.model,
            "available": transport.is_available(),
        },
        "vector_store": vs,
        "tools": tools.TOOL_NAMES,
    }


@app.get("/api/meta")
def meta() -> Dict[str, Any]:
    """Dataset provenance and counts, for the UI header/footer."""
    from eu_ai_act import data

    raw = data.load_raw()
    return {
        "citation": data.citation(),
        "source": raw.get("source"),
        "counts": {
            "recitals": len(raw.get("recitals", [])),
            "articles": len(raw.get("articles", [])),
            "annexes": len(raw.get("annexes", [])),
        },
        "tools": tools.TOOL_NAMES,
    }


@app.get("/api/tools")
def tool_schemas() -> List[Dict[str, Any]]:
    return tools.TOOL_SCHEMAS


# ---------------------------------------------------------------------------
# AG-UI endpoint
# ---------------------------------------------------------------------------
@app.post("/agent")
async def run_agent_endpoint(request: Request) -> StreamingResponse:
    """Run the agent and stream AG-UI events over SSE."""
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    inp = agui.RunAgentInput.from_dict(body if isinstance(body, dict) else {})

    forwarded = inp.forwarded_props or {}
    transport = OpenAICompatibleTransport(
        model=forwarded.get("model"),
        temperature=float(forwarded.get("temperature", 0.2)),
    )

    events = agent_mod.run_agent(inp, transport)
    return StreamingResponse(
        agui.encode_stream(events),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# REST passthrough (deterministic, no model call)
# ---------------------------------------------------------------------------
def _run(tool: str, args: Optional[Dict[str, Any]] = None) -> Any:
    try:
        return tools.execute(tool, args or {})
    except tools.ToolError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"{type(exc).__name__}: {exc}") from exc


def _with_markdown(result: Any) -> Any:
    """
    Attach the Markdown rendering of a provision's text.

    The agent keeps working from the raw `text`; only the browser needs the
    formatted copy, so it is added here rather than in the tool.
    """
    if isinstance(result, dict) and result.get("text"):
        from eu_ai_act import formatting

        result["markdown"] = formatting.to_markdown(result["text"], result.get("title"))
    return result


@app.get("/api/search")
def api_search(
    q: str = Query(..., min_length=1),
    scope: str = Query("all"),
    limit: int = Query(20, ge=1, le=100),
) -> Any:
    return _run("search_act", {"query": q, "scope": scope, "limit": limit})


@app.get("/api/articles")
def api_articles() -> Any:
    """Index of every article (number + title), for the explorer's table of contents."""
    from eu_ai_act import data

    return {"items": [{"number": a["number"], "title": a["title"]}
                      for a in data.load_raw().get("articles", [])]}


@app.get("/api/recitals")
def api_recitals() -> Any:
    from eu_ai_act import data

    return {"items": [{"number": r["number"], "title": r["text"][:90]}
                      for r in data.load_raw().get("recitals", [])]}


@app.get("/api/annexes")
def api_annexes() -> Any:
    from eu_ai_act import data

    return {"items": [{"number": a["number"], "title": a["title"]}
                      for a in data.load_raw().get("annexes", [])]}


@app.get("/api/article/{number}")
def api_article(number: str) -> Any:
    # `full` asks the tool for the unclipped text: the clip guards the model's
    # context, and there is no model in this path — only a reader.
    return _with_markdown(_run("get_article", {"number": number, "full": True}))


@app.get("/api/recital/{number}")
def api_recital(number: int) -> Any:
    return _with_markdown(_run("get_recital", {"number": number, "full": True}))


@app.get("/api/annex/{number}")
def api_annex(number: str) -> Any:
    return _with_markdown(_run("get_annex", {"number": number, "full": True}))


@app.get("/api/tiers")
def api_tiers() -> Any:
    from eu_ai_act import data

    return {"items": data.risk_tiers()}


@app.get("/api/tiers/{tier}")
def api_tier(tier: str) -> Any:
    return _run("risk_tier", {"tier": tier})


@app.get("/api/actors")
def api_actors() -> Any:
    from eu_ai_act import data

    return {"items": data.actors()}


@app.get("/api/actors/{actor}")
def api_actor(actor: str) -> Any:
    return _run("actor_obligations", {"actor": actor})


@app.get("/api/checklist/{actor}")
def api_checklist(actor: str, tier: Optional[str] = Query(None)) -> Any:
    return _run("compliance_checklist", {"actor": actor, "tier": tier})


@app.get("/api/classify")
def api_classify(description: str = Query(..., min_length=1)) -> Any:
    return _run("classify_high_risk", {"description": description})


@app.get("/api/timeline")
def api_timeline() -> Any:
    return _run("timeline")


@app.get("/api/penalties")
def api_penalties() -> Any:
    return _run("penalties")


@app.get("/api/definitions")
def api_definitions(term: Optional[str] = Query(None)) -> Any:
    return _run("definitions", {"term": term} if term else {})


@app.get("/api/governance")
def api_governance() -> Any:
    return _run("governance")


@app.get("/api/crossrefs")
def api_crossrefs(topic: Optional[str] = Query(None)) -> Any:
    return _run("cross_references", {"topic": topic} if topic else {})


# ---------------------------------------------------------------------------
# Navigation, guides, diagrams and statistics
# ---------------------------------------------------------------------------
@app.get("/api/structure")
def api_structure() -> Any:
    """
    The Act's table of contents, shaped for the UI: chapters with their sections
    and the resolved article lists.

    Note this differs from the agent's `structure_of_act` tool, which returns a
    compressed range string ("6-49") because the model only needs to read it.
    """
    from eu_ai_act import structure

    toc = structure.table_of_contents()
    return {
        "ref": "Table of contents",
        "chapters": toc,
        "text": (
            f"{len(toc)} chapters, "
            f"{sum(len(c['sections']) for c in toc)} sections, "
            f"{sum(len(c['articles']) + sum(len(s['articles']) for s in c['sections']) for c in toc)} articles."
        ),
    }


@app.get("/api/structure/{article}")
def api_structure_article(article: str) -> Any:
    return _run("structure_of_act", {"article": article})


@app.get("/api/stats")
def api_stats() -> Any:
    return _run("corpus_stats", {})


@app.get("/api/graph")
def api_graph() -> Any:
    """The whole citation graph between provisions."""
    from eu_ai_act import structure

    graph = structure.citation_graph()
    return {
        "nodes": graph["nodes"],
        "edges": graph["edges"],
        "most_cited": graph["most_cited"],
        "edge_count": graph["edge_count"],
    }


@app.get("/api/graph/{article}")
def api_graph_article(article: str) -> Any:
    from eu_ai_act import structure

    return {
        "ref": f"Article {article}",
        "cites": structure.references_of(article),
        "cited_by": structure.cited_by(article),
    }


@app.get("/api/procedures")
def api_procedures() -> Any:
    return _run("procedures", {})


@app.get("/api/procedures/{procedure_id}")
def api_procedure(procedure_id: str) -> Any:
    return _run("procedures", {"id": procedure_id})


@app.get("/api/scenarios")
def api_scenarios() -> Any:
    return _run("scenarios", {})


@app.get("/api/scenarios/{scenario_id}")
def api_scenario(scenario_id: str) -> Any:
    return _run("scenarios", {"id": scenario_id})


@app.get("/api/risk-path")
def api_risk_path() -> Any:
    """The classification ladder: questions, branches and tier outcomes."""
    from eu_ai_act import guides

    return guides.risk_path()


@app.post("/api/risk-path/classify")
async def api_risk_path_classify(request: Request) -> Any:
    """Walk the ladder with the answers supplied; returns the tier or the next question."""
    from eu_ai_act import guides

    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    answers = (body or {}).get("answers") or {}
    return guides.classify_path({k: bool(v) for k, v in answers.items()})


@app.get("/api/governance/structure")
def api_governance_structure() -> Any:
    """The institutional tree, for the organigram."""
    from eu_ai_act import guides

    return guides.governance_structure()


@app.get("/api/mindmaps")
def api_mindmaps() -> Any:
    from eu_ai_act import mindmap

    return {"items": mindmap.topics()}


@app.get("/api/mindmaps/chapter/{number}")
def api_mindmap_chapter(number: str) -> Any:
    from eu_ai_act import mindmap

    node = mindmap.chapter_map(number)
    if node is None:
        raise HTTPException(status_code=404, detail=f"No chapter '{number}'.")
    return node


@app.get("/api/mindmaps/{topic}")
def api_mindmap(topic: str) -> Any:
    from eu_ai_act import mindmap

    node = mindmap.build(topic)
    if node is None:
        raise HTTPException(status_code=404, detail=f"No mindmap '{topic}'.")
    return node


# ---------------------------------------------------------------------------
# Provider settings — for running this on your own infrastructure
#
# These do not merely read the provider: they WRITE it, and the /test endpoint
# will probe a URL you hand it. On a public deployment that is not a hidden
# feature but an open door — any visitor could repoint the site's inference at an
# endpoint of their own choosing, or use the deployment to scan the network it
# sits on. So in public mode the routes are off, not just unlinked.
#
# EU_AI_ACT_PUBLIC_MODE=1 (set by the kmail.at deployment) disables them.
# ---------------------------------------------------------------------------
PUBLIC_MODE_ENV = "EU_AI_ACT_PUBLIC_MODE"


def _settings_enabled() -> None:
    # Read at call time, not import time, so the deployment's env is what counts
    # and a test can set it.
    # 404 rather than 403: a blocked endpoint should not advertise that it exists.
    if os.environ.get(PUBLIC_MODE_ENV, "0") == "1":
        raise HTTPException(status_code=404, detail="Not found")


@app.get("/api/settings/provider")
def api_get_settings() -> Any:
    """The saved provider config, what is in effect, and any env var overriding it."""
    _settings_enabled()
    return settings_mod.read_settings()


@app.put("/api/settings/provider")
async def api_put_settings(request: Request) -> Any:
    """Persist provider settings. Omitted fields are left untouched."""
    _settings_enabled()
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="body must be a JSON object")
    return settings_mod.write_settings(body)


@app.post("/api/settings/provider/test")
async def api_test_settings(request: Request) -> Any:
    """
    Probe an OpenAI-compatible endpoint. Send unsaved form values to test them
    before committing; omit them to test what is currently configured.
    """
    _settings_enabled()
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    body = body if isinstance(body, dict) else {}
    return settings_mod.test_connection(
        base_url=body.get("base_url"),
        api_key=body.get("api_key"),
        timeout=body.get("timeout"),
    )


def run() -> None:
    """Console-script entry point: ``python -m app.main``."""
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8000")),
        reload=os.environ.get("RELOAD", "0") == "1",
    )


if __name__ == "__main__":
    run()
