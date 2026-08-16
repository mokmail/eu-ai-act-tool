"""Tests for the search layer."""
from eu_ai_act import search


def test_search_finds_human_oversight():
    results = search.search("human oversight", limit=5)
    assert len(results) > 0
    refs = [r["ref"] for r in results]
    assert "Article 14" in refs  # Human oversight article


def test_search_scope_articles_only():
    results = search.search("biometric", scope="articles", limit=10)
    assert len(results) > 0
    assert all(r["kind"] == "article" for r in results)


def test_search_scope_recitals_only():
    results = search.search("biometric", scope="recitals", limit=10)
    assert len(results) > 0
    assert all(r["kind"] == "recital" for r in results)


def test_search_scope_annexes_only():
    results = search.search("technical documentation", scope="annexes", limit=10)
    assert len(results) > 0
    assert all(r["kind"] == "annex" for r in results)


def test_search_no_results():
    results = search.search("zzzznotawordzzzz")
    assert results == []


def test_search_ranking_by_count():
    results = search.search("AI system", limit=5)
    counts = [r["count"] for r in results]
    assert counts == sorted(counts, reverse=True)


def test_excerpt_contains_query():
    text = "The quick brown fox jumps over the lazy dog."
    ex = search.excerpt(text, "fox")
    assert "fox" in ex
