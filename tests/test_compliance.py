"""Tests for the compliance layer."""
from eu_ai_act import compliance


def test_provider_checklist_has_high_risk_obligations():
    items = compliance.checklist("provider")
    titles = [i["title"] for i in items]
    assert "Establish a risk management system" in titles
    assert "Prepare technical documentation" in titles
    assert "Affix CE marking" in titles


def test_deployer_checklist_has_fria():
    items = compliance.checklist("deployer")
    titles = [i["title"] for i in items]
    assert any("fundamental rights" in t.lower() for t in titles)


def test_checklist_items_have_refs():
    for item in compliance.checklist("provider"):
        assert item["ref"]
        assert item["action"]
        assert item["title"]


def test_obligations_filter_by_tier():
    hr = compliance.obligations_for(tier="high_risk")
    assert len(hr) > 0
    # obligations with tier "all" apply to every tier
    assert all(o["tier"] in ("all", "high_risk") for o in hr)
    # and at least one is specifically high_risk
    assert any(o["tier"] == "high_risk" for o in hr)


def test_obligations_filter_by_actor():
    imp = compliance.obligations_for(actor="importer")
    assert len(imp) > 0
    assert all(o["actor"] in ("all", "importer") for o in imp)


def test_classify_high_risk_biometric():
    result = compliance.classify_high_risk("facial recognition for recruitment")
    assert result["likely_high_risk"] is True
    assert len(result["matched_annex_iii_areas"]) >= 1


def test_classify_not_high_risk():
    result = compliance.classify_high_risk("a simple calculator app")
    assert result["likely_high_risk"] is False


def test_classify_has_disclaimer():
    result = compliance.classify_high_risk("anything")
    assert "disclaimer" in result
