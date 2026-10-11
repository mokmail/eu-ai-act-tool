"""
Provider settings — read, write and test the AI backend configuration.

The app runs against any OpenAI-compatible endpoint: a local Ollama, a cloud
gateway, or a self-hosted vLLM / llama.cpp server. This module is the single
place that reads and writes the provider config file and reports what is
*actually in effect*.

Two things it is careful about:

* **Environment beats the file.** That is how you configure a container, so a
  saved setting that an env var overrides would look like a broken form. The
  response names the overriding variable instead of hiding it.
* **The API key never leaves the server.** Reads report only whether one is set;
  writes accept one, or a flag to clear it.

Note: the write endpoint is unauthenticated, by design — this is a tool you run
yourself. Bind the server to localhost (the default) or put it behind whatever
auth your infrastructure already has before exposing it.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx

from eu_ai_act.ai_provider import CONFIG_PATH

from .llm import load_provider_config

# Only the variables the server actually honours. Claiming more would be a lie.
ENV_VARS: Dict[str, str] = {
    "base_url": "EU_AI_ACT_BASE_URL",
    "chat_model": "EU_AI_ACT_CHAT_MODEL",
    "api_key": "EU_AI_ACT_API_KEY",
}


def config_path() -> str:
    """Where the config is read from and written to (overridable, for tests)."""
    return os.environ.get("EU_AI_ACT_CONFIG_PATH") or CONFIG_PATH


def _env_overrides() -> Dict[str, str]:
    return {field: var for field, var in ENV_VARS.items() if os.environ.get(var)}


def effective() -> Dict[str, Any]:
    """What a request will actually use, after environment precedence."""
    from .llm import OpenAICompatibleTransport

    transport = OpenAICompatibleTransport()
    return {
        "base_url": transport.base_url,
        "chat_model": transport.model,
        "timeout": transport.timeout,
    }


def read_settings() -> Dict[str, Any]:
    """The saved config, what is in effect, and which env vars are overriding."""
    cfg = load_provider_config()
    return {
        "config": {
            "base_url": cfg.base_url,
            "chat_model": cfg.chat_model,
            "embed_model": cfg.embed_model,
            "timeout": cfg.timeout,
            "api_key_set": bool(cfg.api_key),
        },
        "effective": effective(),
        "env_overrides": _env_overrides(),
        "config_path": config_path(),
    }


def write_settings(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Persist the submitted fields, leaving anything omitted untouched."""
    path = config_path()
    cfg = load_provider_config()

    for field in ("base_url", "chat_model", "embed_model"):
        value = payload.get(field)
        if isinstance(value, str) and value.strip():
            setattr(cfg, field, value.strip())

    if payload.get("clear_api_key"):
        cfg.api_key = None
    elif isinstance(payload.get("api_key"), str) and payload["api_key"].strip():
        cfg.api_key = payload["api_key"].strip()

    if payload.get("timeout") is not None:
        try:
            cfg.timeout = max(5, min(600, int(payload["timeout"])))
        except (TypeError, ValueError):
            pass

    cfg.save(path)
    return read_settings()


def test_connection(
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    timeout: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Probe an OpenAI-compatible endpoint's /models.

    Uses the values passed in when the form has not been saved yet, so you can
    test before committing a change.
    """
    cfg = load_provider_config()
    base = (base_url or "").strip() or os.environ.get("EU_AI_ACT_BASE_URL") or cfg.base_url
    key = (api_key or "").strip() or os.environ.get("EU_AI_ACT_API_KEY") or cfg.api_key
    wait = float(timeout or cfg.timeout or 30)
    url = base.rstrip("/") + "/models"

    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"

    try:
        response = httpx.get(url, timeout=min(wait, 20), headers=headers)
    except Exception as exc:  # noqa: BLE001 - any transport failure is the answer
        return {"reachable": False, "url": url, "error": f"{type(exc).__name__}: {exc}"}

    if response.status_code != 200:
        return {
            "reachable": False,
            "url": url,
            "error": f"HTTP {response.status_code} — {response.text[:200]}",
        }

    try:
        data = response.json()
    except ValueError:
        return {"reachable": False, "url": url, "error": "response was not JSON"}

    models: List[str] = sorted({
        str(m.get("id") or m.get("name"))
        for m in data.get("data", [])
        if m.get("id") or m.get("name")
    })
    return {"reachable": True, "url": url, "models": models}
