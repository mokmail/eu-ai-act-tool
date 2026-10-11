"""
Provider settings: reading, writing and probing the AI backend configuration.

Every test points EU_AI_ACT_CONFIG_PATH at a throwaway file so the developer's own
~/.config/eu-ai-act/provider.json is never touched.
"""
from __future__ import annotations

import json
from typing import Any, Dict

import pytest

from app import settings


@pytest.fixture()
def cfg(tmp_path, monkeypatch):
    """An isolated config file, and a clean environment."""
    path = tmp_path / "provider.json"
    monkeypatch.setenv("EU_AI_ACT_CONFIG_PATH", str(path))
    for var in ("EU_AI_ACT_BASE_URL", "EU_AI_ACT_CHAT_MODEL", "EU_AI_ACT_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    return path


# -- reading ----------------------------------------------------------------
def test_defaults_when_nothing_is_configured(cfg):
    body = settings.read_settings()
    assert body["config"]["base_url"] == "http://localhost:11434/v1"
    assert body["config"]["api_key_set"] is False
    assert body["config"]["timeout"] == 120
    assert body["config_path"] == str(cfg)
    assert body["env_overrides"] == {}


def test_read_never_returns_the_api_key(cfg):
    settings.write_settings({"api_key": "sk-secret-value"})
    body = settings.read_settings()
    assert body["config"]["api_key_set"] is True
    assert "sk-secret-value" not in json.dumps(body)


def test_effective_reflects_the_saved_file(cfg):
    settings.write_settings({"base_url": "http://box:8000/v1", "chat_model": "my-model"})
    effective = settings.read_settings()["effective"]
    assert effective["base_url"] == "http://box:8000/v1"
    assert effective["chat_model"] == "my-model"


# -- environment precedence -------------------------------------------------
def test_env_vars_are_reported_as_overrides(cfg, monkeypatch):
    monkeypatch.setenv("EU_AI_ACT_BASE_URL", "http://env-host:1234/v1")
    monkeypatch.setenv("EU_AI_ACT_CHAT_MODEL", "env-model")
    body = settings.read_settings()
    assert body["env_overrides"] == {
        "base_url": "EU_AI_ACT_BASE_URL",
        "chat_model": "EU_AI_ACT_CHAT_MODEL",
    }
    # the file still holds the old value; the env var is what wins
    assert body["config"]["base_url"] == "http://localhost:11434/v1"
    assert body["effective"]["base_url"] == "http://env-host:1234/v1"


def test_only_variables_the_server_honours_are_reported(cfg, monkeypatch):
    monkeypatch.setenv("EU_AI_ACT_EMBED_MODEL", "something")
    assert "embed_model" not in settings.read_settings()["env_overrides"]


# -- writing ----------------------------------------------------------------
def test_write_persists_and_round_trips(cfg):
    settings.write_settings({
        "base_url": "http://gpu-01:8000/v1",
        "chat_model": "qwen3-32b",
        "embed_model": "bge-m3",
        "timeout": 45,
    })
    saved = json.loads(cfg.read_text())
    assert saved["base_url"] == "http://gpu-01:8000/v1"
    assert saved["chat_model"] == "qwen3-32b"
    assert saved["timeout"] == 45


def test_write_leaves_omitted_fields_alone(cfg):
    settings.write_settings({"base_url": "http://a:1/v1", "chat_model": "m1"})
    settings.write_settings({"chat_model": "m2"})
    body = settings.read_settings()
    assert body["config"]["base_url"] == "http://a:1/v1"
    assert body["config"]["chat_model"] == "m2"


def test_api_key_can_be_set_and_cleared(cfg):
    settings.write_settings({"api_key": "sk-1"})
    assert settings.read_settings()["config"]["api_key_set"] is True
    settings.write_settings({"clear_api_key": True})
    assert settings.read_settings()["config"]["api_key_set"] is False


def test_blank_values_are_ignored_rather_than_wiping_fields(cfg):
    settings.write_settings({"base_url": "http://keep:1/v1", "chat_model": "keep-me"})
    settings.write_settings({"base_url": "   ", "chat_model": "", "api_key": "  "})
    body = settings.read_settings()
    assert body["config"]["base_url"] == "http://keep:1/v1"
    assert body["config"]["chat_model"] == "keep-me"


def test_timeout_is_clamped(cfg):
    assert settings.write_settings({"timeout": 1})["config"]["timeout"] == 5
    assert settings.write_settings({"timeout": 99999})["config"]["timeout"] == 600
    assert settings.write_settings({"timeout": "abc"})["config"]["timeout"] == 600


# -- probing ----------------------------------------------------------------
def test_probe_reports_an_unreachable_host(cfg):
    result = settings.test_connection(base_url="http://127.0.0.1:9/v1", timeout=1)
    assert result["reachable"] is False
    assert result["url"] == "http://127.0.0.1:9/v1/models"
    assert result["error"]


def test_probe_reports_a_non_200(cfg, monkeypatch):
    class FakeResponse:
        status_code = 401
        text = "unauthorized"

        def json(self):
            return {}

    monkeypatch.setattr(settings.httpx, "get", lambda *a, **k: FakeResponse())
    result = settings.test_connection(base_url="http://x/v1")
    assert result["reachable"] is False
    assert "401" in result["error"]


def test_probe_lists_models_on_success(cfg, monkeypatch):
    class FakeResponse:
        status_code = 200
        text = ""

        def json(self):
            return {"data": [{"id": "llama3.2:latest"}, {"id": "qwen3:32b"},
                             {"name": "no-id-model"}, {"id": "llama3.2:latest"}]}

    monkeypatch.setattr(settings.httpx, "get", lambda *a, **k: FakeResponse())
    result = settings.test_connection(base_url="http://x/v1")
    assert result["reachable"] is True
    assert result["models"] == ["llama3.2:latest", "no-id-model", "qwen3:32b"]


def test_probe_falls_back_to_the_saved_config(cfg):
    settings.write_settings({"base_url": "http://saved-host:9/v1"})
    assert settings.test_connection(timeout=1)["url"] == "http://saved-host:9/v1/models"


def test_probe_sends_the_key_as_a_bearer_token(cfg, monkeypatch):
    seen: Dict[str, Any] = {}

    class FakeResponse:
        status_code = 200
        text = ""

        def json(self):
            return {"data": []}

    def fake_get(url, timeout=None, headers=None):
        seen["headers"] = headers or {}
        return FakeResponse()

    monkeypatch.setattr(settings.httpx, "get", fake_get)
    settings.write_settings({"base_url": "http://x/v1", "api_key": "sk-abc"})
    settings.test_connection()
    assert seen["headers"]["Authorization"] == "Bearer sk-abc"


# -- HTTP surface -----------------------------------------------------------
def test_endpoints_round_trip(client, cfg):
    initial = client.get("/api/settings/provider").json()
    assert initial["config"]["base_url"] == "http://localhost:11434/v1"

    saved = client.put("/api/settings/provider", json={
        "base_url": "http://vllm-host:8000/v1",
        "chat_model": "mistral-small",
        "api_key": "sk-live",
    }).json()
    assert saved["config"]["base_url"] == "http://vllm-host:8000/v1"
    assert saved["config"]["chat_model"] == "mistral-small"
    assert saved["config"]["api_key_set"] is True

    again = client.get("/api/settings/provider").json()
    assert again["config"]["base_url"] == "http://vllm-host:8000/v1"


def test_endpoint_rejects_a_non_object_body(client, cfg):
    assert client.put("/api/settings/provider", json=[1, 2, 3]).status_code == 400


def test_test_endpoint_does_not_500_on_a_dead_host(client, cfg):
    result = client.post("/api/settings/provider/test",
                         json={"base_url": "http://127.0.0.1:9/v1", "timeout": 1}).json()
    assert result["reachable"] is False
    assert result["error"]


def test_test_endpoint_tolerates_an_empty_body(client, cfg):
    assert client.post("/api/settings/provider/test", json={}).status_code == 200
