"""Tool registry: dispatch, arguments, error handling, and every grounded call."""
import pytest

from app import tools


def test_every_schema_has_a_handler():
    for schema in tools.TOOL_SCHEMAS:
        name = schema["function"]["name"]
        assert name in tools._HANDLERS, f"{name} has no handler"
    assert set(tools.TOOL_NAMES) == set(tools._HANDLERS)


def test_schemas_are_openai_function_shaped():
    for schema in tools.TOOL_SCHEMAS:
        assert schema["type"] == "function"
        fn = schema["function"]
        assert fn["name"] and fn["description"]
        assert fn["parameters"]["type"] == "object"


def test_unknown_tool_raises():
    with pytest.raises(tools.ToolError):
        tools.execute("does_not_exist", {})


def test_get_article_returns_cited_text():
    result = tools.execute("get_article", {"number": "5"})
    assert result["ref"] == "Article 5"
    assert "prohibited" in result["text"].lower()
    assert result["title"]


def test_get_recital_and_annex():
    assert tools.execute("get_recital", {"number": 12})["ref"] == "Recital 12"
    annex = tools.execute("get_annex", {"number": "III"})
    assert annex["ref"] == "Annex III"
    assert annex["title"]


def test_get_article_missing_is_graceful():
    result = tools.execute("get_article", {"number": "999"})
    assert "not found" in result["text"]


def test_search_act_ranks_and_excerpts():
    result = tools.execute("search_act", {"query": "human oversight", "limit": 3})
    assert result["result_count"] >= 1
    assert all("ref" in item and "excerpt" in item for item in result["items"])


def test_search_act_empty_query_raises():
    with pytest.raises(tools.ToolError):
        tools.execute("search_act", {"query": "   "})


def test_risk_tier_returns_annex_iii_area_count():
    tier = tools.execute("risk_tier", {"tier": "high_risk"})
    assert tier["title"]
    assert len(tier["areas"]) == 8


def test_actor_obligations_lists_items():
    result = tools.execute("actor_obligations", {"actor": "provider"})
    assert result["items"]
    assert all("ref" in i for i in result["items"])


def test_compliance_checklist_counts_and_citations():
    result = tools.execute("compliance_checklist", {"actor": "provider"})
    assert result["count"] == len(result["items"]) > 0
    assert all(i["ref"] for i in result["items"])


def test_classify_high_risk_flags_recruitment():
    result = tools.execute("classify_high_risk",
                           {"description": "facial recognition for recruitment"})
    assert result["likely_high_risk"] is True
    assert any(a["area"] in (1, 4) for a in result["areas"])
    assert result["disclaimer"]


def test_classify_high_risk_negative_case():
    result = tools.execute("classify_high_risk",
                           {"description": "a spam filter for my inbox"})
    assert result["likely_high_risk"] is False


def test_timeline_penalties_definitions_governance_crossrefs():
    assert tools.execute("timeline")["items"]
    assert tools.execute("penalties")["items"]
    assert tools.execute("definitions")["items"]
    assert tools.execute("governance")["items"]
    assert tools.execute("cross_references")["items"]


def test_definitions_single_term():
    result = tools.execute("definitions", {"term": "provider"})
    assert result["term"] == "provider"
    assert result["definition"]


def test_results_are_json_serialisable():
    import json

    for name in tools.TOOL_NAMES:
        if name == "semantic_search":
            continue  # needs the vector store
        # call with a minimal valid argument set
        args = {
            "search_act": {"query": "ai"},
            "get_article": {"number": "1"},
            "get_recital": {"number": 1},
            "get_annex": {"number": "I"},
            "risk_tier": {"tier": "high_risk"},
            "actor_obligations": {"actor": "provider"},
            "compliance_checklist": {"actor": "provider"},
            "classify_high_risk": {"description": "credit scoring"},
            "provision_references": {"article": "5"},
        }.get(name, {})
        json.dumps(tools.execute(name, args))


def test_the_browser_gets_the_whole_provision_not_the_agents_clip():
    """
    The 6000-character clip guards the model's context. Eight articles exceed it —
    Article 3 runs to 17k — and the browser is asking for the article, not for a
    digest of it.
    """
    clipped3 = tools.execute("get_article", {"number": "3"})["text"]
    full3 = tools.execute("get_article", {"number": "3", "full": True})["text"]

    assert len(clipped3) <= 6100, "the agent's clip should still apply"
    assert len(full3) > 15_000, f"Article 3 is ~17k characters, got {len(full3)}"
    assert "widespread infringement" in full3, "the tail of Article 3 must survive"

    for tool, args in (("get_article", {"number": "113"}), ("get_annex", {"number": "I"})):
        assert len(tools.execute(tool, {**args, "full": True})["text"]) >= len(
            tools.execute(tool, args)["text"]
        )


def test_a_procedure_detail_is_a_superset_of_its_list_entry():
    """
    The list entry and the detail are the same record in two shapes, and the UI
    renders the detail. If the detail drops a field the list carries, the panel
    silently blanks — which is exactly how `tier` went missing once.
    """
    listing = tools.execute("procedures", {})
    assert listing["items"], "no procedures to check"

    for item in listing["items"]:
        detail = tools.execute("procedures", {"id": item["id"]})
        for field in ("id", "title", "ref", "actor", "tier", "summary"):
            assert field in detail, f"procedure '{item['id']}' lost '{field}' from its detail"
            assert detail[field] == item[field], f"'{field}' differs between list and detail"
        assert len(detail["steps"]) == item["steps"]


def test_a_scenario_detail_keeps_the_fields_the_list_carries():
    """The same superset rule, for the cases rather than the procedures."""
    listing = tools.execute("scenarios", {})
    assert listing["items"], "no scenarios to check"

    for item in listing["items"]:
        detail = tools.execute("scenarios", {"id": item["id"]})
        for field in ("id", "title", "sector", "tier", "refs"):
            assert field in detail, f"scenario '{item['id']}' lost '{field}' from its detail"
