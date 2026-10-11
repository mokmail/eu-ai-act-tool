"""Shared test fixtures: a deterministic stand-in for the chat backend."""
from __future__ import annotations

from typing import Any, Dict, Iterator, List, Optional

import pytest
from fastapi.testclient import TestClient

from app import main


class FakeTransport:
    """A deterministic stand-in for the chat backend — no model, no network."""

    model = "fake-model"
    base_url = "http://fake.local/v1"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def is_available(self) -> bool:
        return True

    def stream(self, messages: List[Dict[str, Any]],
               tools: Optional[List[Dict[str, Any]]] = None) -> Iterator[Dict[str, Any]]:
        yield {"type": "text", "delta": "Article 5 "}
        yield {"type": "text", "delta": "bans prohibited practices."}
        yield {"type": "finish", "reason": "stop"}


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(main, "OpenAICompatibleTransport", FakeTransport)
    return TestClient(main.app)
