"""
Streaming chat transport for the agent.

Wraps any OpenAI-compatible ``/chat/completions`` endpoint (local Ollama by
default, Ollama Cloud or any other compatible server via config) and normalises
its SSE stream into a tiny, transport-agnostic chunk protocol:

    {"type": "text",       "delta": "..."}                       # assistant text
    {"type": "tool_call",  "index": 0, "id": str|None,
                           "name": str|None, "args_delta": "..."} # a call fragment
    {"type": "finish",     "reason": "stop"|"tool_calls"|...}    # turn end

Keeping the transport this thin is what makes ``agent.run_agent`` testable with a
scripted transport — no model, no network, no server.

Configuration is read from (in order) explicit arguments, the environment, then
the tool's own ``~/.config/eu-ai-act/provider.json``:

    EU_AI_ACT_BASE_URL    default http://localhost:11434/v1
    EU_AI_ACT_API_KEY     default none
    EU_AI_ACT_CHAT_MODEL  default deepseek-v4.1-flash:cloud (tool-calling capable)
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterator, List, Optional

import httpx

DEFAULT_BASE_URL = "http://localhost:11434/v1"
# Small local instruct models frequently narrate a tool call in prose instead of
# emitting one, so the default needs solid tool-calling. Note that Ollama Cloud
# retires models regularly; if a model starts answering HTTP 410 Gone, pick
# another from `curl localhost:11434/api/tags`.
DEFAULT_CHAT_MODEL = "deepseek-v4.1-flash:cloud"


def _tool_provider_config() -> Dict[str, Any]:
    """Read the tool's own provider config, if present, without importing chromadb."""
    cfg = load_provider_config()
    return {
        "base_url": cfg.base_url,
        "api_key": cfg.api_key,
        "chat_model": cfg.chat_model,
        "timeout": cfg.timeout,
    }


def load_provider_config():
    """
    Load the provider config, honouring EU_AI_ACT_CONFIG_PATH.

    The override exists so tests (and multi-instance deploys) can point at their
    own config file instead of ~/.config/eu-ai-act/provider.json.
    """
    from eu_ai_act.ai_provider import ProviderConfig

    try:
        return ProviderConfig.load(os.environ.get("EU_AI_ACT_CONFIG_PATH") or None)
    except Exception:  # noqa: BLE001 - a broken config must not stop the server
        return ProviderConfig()


class OpenAICompatibleTransport:
    """Sync, streaming, tool-calling transport over an OpenAI-compatible API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
        temperature: float = 0.2,
    ):
        cfg = _tool_provider_config()
        self.base_url = (base_url or os.environ.get("EU_AI_ACT_BASE_URL")
                         or cfg["base_url"]).rstrip("/")
        self.api_key = api_key or os.environ.get("EU_AI_ACT_API_KEY") or cfg["api_key"]
        # The config file must be consulted too, or setting chat_model in the
        # settings page would silently do nothing.
        self.model = (model or os.environ.get("EU_AI_ACT_CHAT_MODEL")
                      or cfg["chat_model"] or DEFAULT_CHAT_MODEL)
        self.timeout = float(timeout or cfg["timeout"] or 120)
        self.temperature = temperature

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def is_available(self) -> bool:
        try:
            r = httpx.get(f"{self.base_url}/models", timeout=5,
                          headers=self._headers())
            return r.status_code == 200
        except httpx.HTTPError:
            return False

    def stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Stream one assistant turn, yielding normalised chunks."""
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "temperature": self.temperature,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        with httpx.Client(base_url=self.base_url, timeout=self.timeout,
                          headers=self._headers()) as client:
            with client.stream("POST", "/chat/completions", json=payload) as resp:
                resp.raise_for_status()
                for raw in resp.iter_lines():
                    if not raw:
                        continue
                    line = raw.strip()
                    if not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if data == "[DONE]":
                        break
                    try:
                        obj = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    for chunk in _normalise(obj):
                        yield chunk


def _normalise(obj: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
    choices = obj.get("choices") or []
    if not choices:
        return
    choice = choices[0]
    delta = choice.get("delta") or {}
    content = delta.get("content")
    if content:
        yield {"type": "text", "delta": content}
    for tc in delta.get("tool_calls") or []:
        fn = tc.get("function") or {}
        yield {
            "type": "tool_call",
            "index": int(tc.get("index") or 0),
            "id": tc.get("id"),
            "name": fn.get("name"),
            "args_delta": fn.get("arguments") or "",
        }
    reason = choice.get("finish_reason")
    if reason:
        yield {"type": "finish", "reason": reason}
