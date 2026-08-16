"""Tests for the CLI layer."""
import json

from eu_ai_act import cli


def test_citation_command(capsys):
    assert cli.main(["citation"]) == 0
    out = capsys.readouterr().out
    assert "2024/1689" in out


def test_article_command(capsys):
    assert cli.main(["article", "5"]) == 0
    out = capsys.readouterr().out
    assert "Prohibited AI practices" in out


def test_article_json(capsys):
    assert cli.main(["article", "5", "--json"]) == 0
    out = capsys.readouterr().out
    d = json.loads(out)
    assert d["number"] == "5"


def test_timeline_command(capsys):
    assert cli.main(["timeline"]) == 0
    out = capsys.readouterr().out
    assert "2026-08-02" in out


def test_penalties_command(capsys):
    assert cli.main(["penalties"]) == 0
    out = capsys.readouterr().out
    assert "35,000,000" in out


def test_tier_command(capsys):
    assert cli.main(["tier", "high_risk"]) == 0
    out = capsys.readouterr().out
    assert "High-risk AI systems" in out


def test_actor_command(capsys):
    assert cli.main(["actor", "deployer"]) == 0
    out = capsys.readouterr().out
    assert "Deployer" in out


def test_checklist_command(capsys):
    assert cli.main(["checklist", "provider"]) == 0
    out = capsys.readouterr().out
    assert "COMPLIANCE CHECKLIST" in out


def test_search_command(capsys):
    assert cli.main(["search", "human oversight", "--limit", "3"]) == 0
    out = capsys.readouterr().out
    assert "SEARCH" in out


def test_classify_command(capsys):
    assert cli.main(["classify", "facial", "recognition", "for", "recruitment"]) == 0
    out = capsys.readouterr().out
    assert "LIKELY HIGH-RISK" in out


def test_unknown_article_returns_zero_but_prints_not_found(capsys):
    assert cli.main(["article", "999"]) == 0
    out = capsys.readouterr().out
    assert "not found" in out
