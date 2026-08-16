"""Tests for the RAG layer (no live Ollama required)."""
from eu_ai_act import ai_rag


def test_direct_provision_article():
    p = ai_rag._direct_provision("Article 5")
    assert p is not None
    assert p["ref"] == "Article 5"
    assert "prohibited" in p["text"].lower()


def test_direct_provision_recital():
    p = ai_rag._direct_provision("Recital 1")
    assert p is not None
    assert p["ref"] == "Recital 1"


def test_direct_provision_annex():
    p = ai_rag._direct_provision("Annex III")
    assert p is not None
    assert p["ref"] == "Annex III"


def test_direct_provision_invalid():
    assert ai_rag._direct_provision("Not a provision") is None


def test_direct_provision_missing_number_article():
    # Regression: "Article" with no number must not raise IndexError.
    assert ai_rag._direct_provision("Article") is None


def test_direct_provision_missing_number_recital():
    assert ai_rag._direct_provision("Recital") is None


def test_direct_provision_missing_number_annex():
    assert ai_rag._direct_provision("Annex") is None


def test_direct_provision_non_numeric_recital():
    assert ai_rag._direct_provision("Recital twelve") is None


def test_obligations_provider():
    result = ai_rag.obligations(actor="provider")
    assert result["answer"]
    assert "Article" in result["sources"][0]


def test_obligations_tier():
    result = ai_rag.obligations(tier="high_risk")
    assert result["answer"]
    assert len(result["sources"]) > 0


def test_extract_sources():
    context = "[Article 5] text [Recital 12] more [Article 5]"
    sources = ai_rag._extract_sources(context)
    assert "Article 5" in sources
    assert "Recital 12" in sources
    # deduplicated
    assert sources.count("Article 5") == 1
