"""HTTP layer: the AG-UI SSE endpoint and the REST passthrough (transport faked)."""
from __future__ import annotations

import json
from typing import List

from app import main


def sse_events(text: str) -> List[dict]:
    out = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            out.append(json.loads(line[len("data:"):].strip()))
    return out


# -- health / meta -----------------------------------------------------------
def test_health_reports_provider_and_tools(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["provider"]["available"] is True
    assert "search_act" in body["tools"]
    assert "vector_store" in body


def test_meta_reports_provenance_and_counts(client):
    body = client.get("/api/meta").json()
    assert "2024/1689" in body["citation"]
    assert body["counts"]["articles"] == 113
    assert body["counts"]["recitals"] == 180
    assert body["counts"]["annexes"] == 13


def test_tools_endpoint_returns_schemas(client):
    body = client.get("/api/tools").json()
    assert isinstance(body, list)
    names = [t["function"]["name"] for t in body]
    assert "get_article" in names


# -- AG-UI endpoint ----------------------------------------------------------
def test_agent_streams_agui_events(client):
    resp = client.post("/agent", json={
        "threadId": "t1", "runId": "r1",
        "messages": [{"role": "user", "content": "What does Article 5 prohibit?"}],
    })
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")

    events = sse_events(resp.text)
    kinds = [e["type"] for e in events]
    assert kinds[0] == "RUN_STARTED"
    assert kinds[-1] == "RUN_FINISHED"
    assert "TEXT_MESSAGE_START" in kinds
    assert "TEXT_MESSAGE_END" in kinds

    text = "".join(e["delta"] for e in events if e["type"] == "TEXT_MESSAGE_CONTENT")
    assert text == "Article 5 bans prohibited practices."


def test_agent_tolerates_an_empty_body(client):
    resp = client.post("/agent", json={})
    assert resp.status_code == 200
    events = sse_events(resp.text)
    assert events[0]["type"] == "RUN_STARTED"
    assert events[-1]["type"] == "RUN_FINISHED"


def test_agent_every_frame_is_a_single_sse_message(client):
    resp = client.post("/agent", json={"messages": [{"role": "user", "content": "hi"}]})
    frames = [f for f in resp.text.split("\n\n") if f.strip()]
    for frame in frames:
        assert frame.strip().startswith("data: ")
        json.loads(frame.strip()[len("data:"):].strip())


# -- REST passthrough --------------------------------------------------------
def test_api_article(client):
    body = client.get("/api/article/5").json()
    assert body["ref"] == "Article 5"
    assert "prohibited" in body["text"].lower()


def test_api_recital_and_annex(client):
    assert client.get("/api/recital/12").json()["ref"] == "Recital 12"
    assert client.get("/api/annex/III").json()["ref"] == "Annex III"


def test_api_search(client):
    body = client.get("/api/search", params={"q": "human oversight", "limit": 3}).json()
    assert body["result_count"] >= 1


def test_api_search_requires_query(client):
    assert client.get("/api/search").status_code == 422


def test_api_tiers(client):
    assert len(client.get("/api/tiers").json()["items"]) == 4
    assert client.get("/api/tiers/high_risk").json()["title"]


def test_api_actors(client):
    assert len(client.get("/api/actors").json()["items"]) == 6
    assert client.get("/api/actors/provider").json()["items"]


def test_api_checklist(client):
    body = client.get("/api/checklist/provider", params={"tier": "high_risk"}).json()
    assert body["count"] > 0
    assert all(i["ref"] for i in body["items"])


def test_api_classify(client):
    body = client.get("/api/classify",
                      params={"description": "credit scoring for loans"}).json()
    assert body["likely_high_risk"] is True


def test_api_reference_endpoints(client):
    assert client.get("/api/timeline").json()["items"]
    assert client.get("/api/penalties").json()["items"]
    assert client.get("/api/definitions").json()["items"]
    assert client.get("/api/governance").json()["items"]
    assert client.get("/api/crossrefs").json()["items"]


def test_api_unknown_article_is_not_a_500(client):
    assert client.get("/api/article/999").status_code == 200


# -- public mode ------------------------------------------------------------
def test_settings_endpoints_are_available_when_not_public(client):
    """Self-hosted: the operator can still configure their own provider."""
    assert client.get("/api/settings/provider").status_code == 200


def test_public_mode_closes_the_settings_endpoints(client, monkeypatch):
    """
    Hidden in the UI is not closed. The PUT writes the deployment's provider and
    the /test route probes a URL the caller chooses, so on a public deployment
    both must be shut, or any visitor can repoint the site's inference.
    """
    monkeypatch.setenv(main.PUBLIC_MODE_ENV, "1")

    assert client.get("/api/settings/provider").status_code == 404
    assert client.put("/api/settings/provider", json={"base_url": "http://evil.local/v1"}).status_code == 404
    assert client.post("/api/settings/provider/test", json={"base_url": "http://evil.local/v1"}).status_code == 404

    # 404, not 403 — a blocked route should not confirm it exists.
    assert client.get("/api/settings/provider").json() == {"detail": "Not found"}


def test_public_mode_still_serves_the_rest_of_the_api(client, monkeypatch):
    """Closing settings must not take the whole app with it."""
    monkeypatch.setenv(main.PUBLIC_MODE_ENV, "1")

    assert client.get("/health").status_code == 200
    assert client.get("/api/meta").status_code == 200
    assert len(client.get("/api/scenarios").json()["items"]) == 50
