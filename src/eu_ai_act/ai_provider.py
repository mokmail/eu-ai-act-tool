"""
AI provider abstraction for the EU AI Act tool.

Default provider is **local Ollama** (http://localhost:11434), which exposes an
OpenAI-compatible API at /v1. When the user is logged into Ollama Cloud, the
same endpoint can reach cloud models (e.g. gemini-3-flash-preview,
mistral-large-3:675b-cloud). The provider is configurable via a JSON config
file so other OpenAI-compatible endpoints can be used.

Config file (default ~/.config/eu-ai-act/provider.json):
{
  "base_url": "http://localhost:11434/v1",
  "chat_model": "mokmail/own:latest",
  "embed_model": "nomic-embed-text:latest",
  "api_key": null,
  "timeout": 120
}
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

DEFAULT_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "eu-ai-act")
CONFIG_PATH = os.path.join(DEFAULT_CONFIG_DIR, "provider.json")

DEFAULT_CONFIG: Dict[str, Any] = {
    "base_url": "http://localhost:11434/v1",
    "chat_model": "mokmail/own:latest",
    "embed_model": "nomic-embed-text:latest",
    "api_key": None,
    "timeout": 120,
}


@dataclass
class ProviderConfig:
    base_url: str = DEFAULT_CONFIG["base_url"]
    chat_model: str = DEFAULT_CONFIG["chat_model"]
    embed_model: str = DEFAULT_CONFIG["embed_model"]
    api_key: Optional[str] = None
    timeout: int = DEFAULT_CONFIG["timeout"]

    @classmethod
    def load(cls, path: Optional[str] = None) -> "ProviderConfig":
        cfg_path = path or CONFIG_PATH
        data = dict(DEFAULT_CONFIG)
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, encoding="utf-8") as f:
                    data.update(json.load(f))
            except (json.JSONDecodeError, OSError):
                pass
        return cls(**data)

    def save(self, path: Optional[str] = None) -> str:
        cfg_path = path or CONFIG_PATH
        os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "base_url": self.base_url,
                    "chat_model": self.chat_model,
                    "embed_model": self.embed_model,
                    "api_key": self.api_key,
                    "timeout": self.timeout,
                },
                f,
                indent=2,
            )
        return cfg_path


class ProviderError(RuntimeError):
    """Raised when the AI provider cannot be reached or returns an error."""


class AIProvider:
    """Client for an OpenAI-compatible chat/embedding endpoint (default Ollama)."""

    def __init__(self, config: Optional[ProviderConfig] = None):
        self.config = config or ProviderConfig.load()
        self._client = httpx.Client(
            base_url=self.config.base_url.rstrip("/"),
            timeout=self.config.timeout,
            headers=self._headers(),
        )

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    # -- health ------------------------------------------------------------
    def is_available(self) -> bool:
        """Check whether the provider is reachable."""
        try:
            r = self._client.get("/models", timeout=5)
            return r.status_code == 200
        except httpx.HTTPError:
            return False

    def list_models(self) -> List[Dict[str, Any]]:
        """List models available on the provider."""
        try:
            r = self._client.get("/models", timeout=10)
            r.raise_for_status()
            data = r.json()
            return data.get("data", [])
        except httpx.HTTPError as e:
            raise ProviderError(f"Could not list models: {e}") from e

    # -- chat --------------------------------------------------------------
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Send a chat completion request and return the assistant's reply."""
        payload: Dict[str, Any] = {
            "model": model or self.config.chat_model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        try:
            r = self._client.post("/chat/completions", json=payload)
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPError as e:
            raise ProviderError(f"Chat request failed: {e}") from e
        except (KeyError, IndexError) as e:
            raise ProviderError(f"Unexpected chat response: {e}") from e

    # -- embeddings --------------------------------------------------------
    def embed(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        """Embed a list of texts using the configured embedding model."""
        if not texts:
            return []
        payload = {
            "model": model or self.config.embed_model,
            "input": texts,
        }
        try:
            r = self._client.post("/embeddings", json=payload)
            r.raise_for_status()
            data = r.json()
            return [item["embedding"] for item in data["data"]]
        except httpx.HTTPError as e:
            raise ProviderError(f"Embedding request failed: {e}") from e
        except (KeyError, IndexError) as e:
            raise ProviderError(f"Unexpected embedding response: {e}") from e

    def close(self) -> None:
        self._client.close()


def get_provider() -> AIProvider:
    return AIProvider()
