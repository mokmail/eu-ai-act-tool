"""
Navigation, guide, diagram and statistics surfaces: the new tools and their HTTP
endpoints. The chat agent and the Explorer UI both depend on these.
"""
from __future__ import annotations

import pytest

from app import tools


# -- tools ------------------------------------------------------------------
def test_structure_tool_returns_the_table_of_contents():
    result = tools.execute("structure_of_act", {})
    assert len(result["chapters"]) == 13
    assert result["chapters"][0]["number"] == "I"
    assert result["chapters"][2]["sections"][0]["articles"] == "6-7"


def test_structure_tool_locates_an_article():
    result = tools.execute("structure_of_act", {"article": "6"})
    assert result["chapter"] == "III"
    assert result["breadcrumb"] == ["Chapter III", "Section 1"]
    assert "Section 1" in result["text"]


def test_structure_tool_handles_an_unknown_article():
    assert "not in the Act" in tools.execute("structure_of_act", {"article": "999"})["text"]


def test_procedures_tool_lists_then_fetches():
    listed = tools.execute("procedures", {})
    assert len(listed["items"]) >= 6
    assert all(i["ref"] for i in listed["items"])

    fria = tools.execute("procedures", {"id": "fria"})
    assert fria["actor"] == "deployer"
    assert fria["steps"][0]["ref"] == "Article 27(1)"


def test_procedures_tool_accepts_a_keyword():
    result = tools.execute("procedures", {"id": "incident"})
    assert result["id"] == "serious-incident"
    assert any(s["ref"].startswith("Article 73") for s in result["steps"])


def test_procedures_tool_reports_what_is_available():
    result = tools.execute("procedures", {"id": "zzzz"})
    assert "No procedure" in result["text"]
    assert result["available"]


def test_scenarios_tool_lists_then_fetches():
    listed = tools.execute("scenarios", {})
    assert len(listed["items"]) >= 6
    assert "not enforcement decisions" in listed["disclaimer"]

    cv = tools.execute("scenarios", {"id": "cv-screening"})
    assert cv["tier"] == "high_risk"
    assert cv["analysis"]
    assert cv["disclaimer"]


def test_corpus_stats_tool():
    result = tools.execute("corpus_stats", {})
    assert result["corpus"]["articles"] == 113
    assert len(result["chapters"]) == 13
    assert result["obligations"]["total"] > 0
    assert "articles" in result["text"]


def test_provision_references_tool_both_directions():
    out = tools.execute("provision_references", {"article": "5", "direction": "out"})
    assert out["cites"]
    assert "cited_by" not in out

    both = tools.execute("provision_references", {"article": "5", "direction": "both"})
    assert both["cites"] and both["cited_by"]


def test_provision_references_requires_an_article():
    with pytest.raises(tools.ToolError):
        tools.execute("provision_references", {})


def test_ranges_helper_compresses_number_lists():
    assert tools._ranges([]) == ""
    assert tools._ranges(["1", "2", "3", "4"]) == "1-4"
    assert tools._ranges(["6"]) == "6"
    assert tools._ranges(["1", "2", "5", "7", "8", "9"]) == "1-2, 5, 7-9"


# -- HTTP endpoints ---------------------------------------------------------
def test_api_structure_endpoints(client):
    toc = client.get("/api/structure").json()
    assert len(toc["chapters"]) == 13
    # The UI shape: article lists, not the agent tool's compressed range strings.
    chapter_iii = next(c for c in toc["chapters"] if c["number"] == "III")
    assert chapter_iii["title"] == "HIGH-RISK AI SYSTEMS"
    assert len(chapter_iii["sections"]) == 5
    assert {"number": "6", "title": "Classification rules for high-risk AI systems"} in \
        chapter_iii["sections"][0]["articles"]
    assert all(isinstance(a["number"], str) for a in chapter_iii["sections"][0]["articles"])

    # chapter.articles is the whole chapter; the UI must not render sections on top of it
    numbers = [a["number"] for c in toc["chapters"] for a in c["articles"]]
    assert len(numbers) == 113
    assert len(set(numbers)) == 113

    located = client.get("/api/structure/53").json()
    assert located["chapter"] == "V"
    assert located["section"] == 2


def test_api_stats(client):
    stats = client.get("/api/stats").json()
    assert stats["corpus"]["articles"] == 113
    assert stats["chapters"]


def test_api_graph_and_per_article_graph(client):
    graph = client.get("/api/graph").json()
    assert graph["edge_count"] > 100
    assert graph["most_cited"][0]["ref"] == "Annex III"
    assert "Article 6" in graph["nodes"]

    one = client.get("/api/graph/6").json()
    assert one["ref"] == "Article 6"
    assert one["cites"]


def test_api_procedures_and_scenarios(client):
    assert client.get("/api/procedures").json()["items"]
    assert client.get("/api/procedures/fria").json()["id"] == "fria"
    assert client.get("/api/scenarios").json()["items"]
    assert client.get("/api/scenarios/cv-screening").json()["tier"] == "high_risk"


def test_api_risk_path_and_classify(client):
    path = client.get("/api/risk-path").json()
    assert path["start"] == "q_prohibited"
    assert len(path["outcomes"]) == 6

    result = client.post("/api/risk-path/classify",
                         json={"answers": {"q_prohibited": True}}).json()
    assert result["complete"] is True
    assert result["outcome"] == "prohibited"

    partial = client.post("/api/risk-path/classify",
                          json={"answers": {"q_prohibited": False}}).json()
    assert partial["complete"] is False
    assert partial["question"]["id"] == "q_annex1"


def test_api_risk_path_classify_tolerates_an_empty_body(client):
    result = client.post("/api/risk-path/classify", json={}).json()
    assert result["question"]["id"] == "q_prohibited"


def test_api_governance_structure(client):
    body = client.get("/api/governance/structure").json()
    assert body["root"]["children"]


def test_api_mindmap_topics(client):
    topics = client.get("/api/mindmaps").json()["items"]
    ids = {t["id"] for t in topics}
    assert {"contents", "high-risk", "governance"} <= ids


def test_api_mindmap_by_topic(client):
    node = client.get("/api/mindmaps/high-risk").json()
    assert node["title"] == "High-risk AI systems"
    assert node["children"]
    assert client.get("/api/mindmaps/nope").status_code == 404


def test_api_mindmap_chapter_route_is_not_shadowed_by_the_topic_route(client):
    node = client.get("/api/mindmaps/chapter/III").json()
    assert node["ref"] == "Chapter III"
    assert node["children"]
    assert client.get("/api/mindmaps/chapter/XCIX").status_code == 404
