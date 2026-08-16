"""Tests for the data loading layer."""
import pytest

from eu_ai_act import data


def test_raw_dataset_has_113_articles():
    arts = data.articles()
    assert len(arts) == 113


def test_raw_dataset_has_180_recitals():
    recs = data.recitals()
    assert len(recs) == 180


def test_raw_dataset_has_13_annexes():
    anns = data.annexes()
    assert len(anns) == 13


def test_article_5_is_prohibited_practices():
    art = data.get_article("5")
    assert art is not None
    assert "prohibited" in art["title"].lower()


def test_article_113_timeline():
    art = data.get_article("113")
    assert art is not None
    assert "2 August 2026" in art["text"]


def test_article_99_penalties():
    art = data.get_article("99")
    assert art is not None
    assert "35 000 000" in art["text"]
    assert "7 %" in art["text"]


def test_article_51_systemic_risk_threshold():
    art = data.get_article("51")
    assert art is not None
    assert "10 25" in art["text"]


def test_curated_has_four_risk_tiers():
    tiers = data.risk_tiers()
    assert [t["tier"] for t in tiers] == [
        "prohibited",
        "high_risk",
        "limited_risk",
        "minimal_risk",
    ]


def test_curated_has_actors():
    actors = data.actors()
    names = [a["actor"] for a in actors]
    assert "provider" in names
    assert "deployer" in names
    assert "importer" in names
    assert "distributor" in names


def test_curated_timeline_has_six_events():
    assert len(data.timeline()) == 6


def test_curated_penalties_have_refs():
    for p in data.penalties():
        assert p["ref"].startswith("Article")


def test_citation():
    assert "2024/1689" in data.citation()
