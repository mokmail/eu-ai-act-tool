"""Tests for the AI provider layer."""
import pytest

from eu_ai_act import ai_provider


def test_default_config():
    cfg = ai_provider.ProviderConfig.load()
    assert cfg.base_url == "http://localhost:11434/v1"
    assert cfg.embed_model == "nomic-embed-text:latest"


def test_config_roundtrip(tmp_path):
    cfg = ai_provider.ProviderConfig(chat_model="test-model")
    path = cfg.save(path=str(tmp_path / "provider.json"))
    loaded = ai_provider.ProviderConfig.load(path)
    assert loaded.chat_model == "test-model"


def test_provider_headers_no_key():
    cfg = ai_provider.ProviderConfig(api_key=None)
    p = ai_provider.AIProvider(cfg)
    assert "Authorization" not in p._headers()
    p.close()


def test_provider_headers_with_key():
    cfg = ai_provider.ProviderConfig(api_key="secret")
    p = ai_provider.AIProvider(cfg)
    assert p._headers()["Authorization"] == "Bearer secret"
    p.close()


def test_embed_empty_list():
    cfg = ai_provider.ProviderConfig()
    p = ai_provider.AIProvider(cfg)
    assert p.embed([]) == []
    p.close()


def test_embed_query_returns_flat_list():
    """embed_query must return a single flat embedding, not a nested list."""
    from eu_ai_act import vector_store

    class FakeProvider:
        config = ai_provider.ProviderConfig(embed_model="test-embed")

        def embed(self, texts):
            return [[0.1, 0.2, 0.3] for _ in texts]

    ef = vector_store.OllamaEmbeddingFunction(FakeProvider())
    result = ef.embed_query("prohibited practices")
    assert isinstance(result, list)
    assert all(isinstance(x, float) for x in result)
    assert result == [0.1, 0.2, 0.3]
