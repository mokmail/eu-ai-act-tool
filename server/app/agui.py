"""
AG-UI protocol (v1.0) wire layer: typed event constructors + an SSE encoder.

AG-UI is an open, event-based protocol that standardises how an agent streams
its work to a user-facing application: one request in (``RunAgentInput``), one
ordered stream of typed events out, carried over Server-Sent Events.

This module is deliberately dependency-free (stdlib only) so the entire protocol
layer is unit-testable with no model, no network and no web framework. The HTTP
adaptation lives in ``main.py``.

Wire format (one SSE message per event)::

    data: {"type":"TEXT_MESSAGE_CONTENT","messageId":"m1","delta":"hi"}\n\n

The event ``type`` is the discriminator, exactly as the official
``@ag-ui/core`` ``EventType`` enum defines it.
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional

# ---------------------------------------------------------------------------
# Event type discriminators (AG-UI 1.0)
# ---------------------------------------------------------------------------
RUN_STARTED = "RUN_STARTED"
RUN_FINISHED = "RUN_FINISHED"
RUN_ERROR = "RUN_ERROR"
STEP_STARTED = "STEP_STARTED"
STEP_FINISHED = "STEP_FINISHED"
TEXT_MESSAGE_START = "TEXT_MESSAGE_START"
TEXT_MESSAGE_CONTENT = "TEXT_MESSAGE_CONTENT"
TEXT_MESSAGE_END = "TEXT_MESSAGE_END"
TOOL_CALL_START = "TOOL_CALL_START"
TOOL_CALL_ARGS = "TOOL_CALL_ARGS"
TOOL_CALL_END = "TOOL_CALL_END"
TOOL_CALL_RESULT = "TOOL_CALL_RESULT"
STATE_SNAPSHOT = "STATE_SNAPSHOT"
STATE_DELTA = "STATE_DELTA"
MESSAGES_SNAPSHOT = "MESSAGES_SNAPSHOT"
RAW = "RAW"
CUSTOM = "CUSTOM"

# Role values used by the message events and RunAgentInput messages.
ROLE_DEVELOPER = "developer"
ROLE_SYSTEM = "system"
ROLE_ASSISTANT = "assistant"
ROLE_USER = "user"
ROLE_TOOL = "tool"


def new_id(prefix: str) -> str:
    """Return a short, unique, prefixed identifier."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _now_ms() -> int:
    return int(time.time() * 1000)


def _event(type_: str, **fields: Any) -> Dict[str, Any]:
    """Attach the common base properties every AG-UI event carries."""
    evt: Dict[str, Any] = {"type": type_, "timestamp": _now_ms()}
    for key, value in fields.items():
        if value is not None:
            evt[key] = value
    return evt


# ---------------------------------------------------------------------------
# Lifecycle events
# ---------------------------------------------------------------------------
def run_started(thread_id: str, run_id: str, parent_run_id: Optional[str] = None,
                input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return _event(RUN_STARTED, threadId=thread_id, runId=run_id,
                  parentRunId=parent_run_id, input=input)


def run_finished(thread_id: str, run_id: str,
                 outcome: Optional[Dict[str, Any]] = None,
                 result: Any = None) -> Dict[str, Any]:
    return _event(RUN_FINISHED, threadId=thread_id, runId=run_id,
                  outcome=outcome, result=result)


def run_error(message: str, code: Optional[str] = None) -> Dict[str, Any]:
    return _event(RUN_ERROR, message=message, code=code)


def step_started(step_name: str) -> Dict[str, Any]:
    return _event(STEP_STARTED, stepName=step_name)


def step_finished(step_name: str) -> Dict[str, Any]:
    return _event(STEP_FINISHED, stepName=step_name)


# ---------------------------------------------------------------------------
# Text message events (Start -> Content* -> End)
# ---------------------------------------------------------------------------
def text_message_start(message_id: str, role: str = ROLE_ASSISTANT) -> Dict[str, Any]:
    return _event(TEXT_MESSAGE_START, messageId=message_id, role=role)


def text_message_content(message_id: str, delta: str) -> Dict[str, Any]:
    return _event(TEXT_MESSAGE_CONTENT, messageId=message_id, delta=delta)


def text_message_end(message_id: str) -> Dict[str, Any]:
    return _event(TEXT_MESSAGE_END, messageId=message_id)


# ---------------------------------------------------------------------------
# Tool call events (Start -> Args* -> End, then exactly one Result)
# ---------------------------------------------------------------------------
def tool_call_start(tool_call_id: str, tool_call_name: str,
                    parent_message_id: Optional[str] = None) -> Dict[str, Any]:
    return _event(TOOL_CALL_START, toolCallId=tool_call_id,
                  toolCallName=tool_call_name, parentMessageId=parent_message_id)


def tool_call_args(tool_call_id: str, delta: str) -> Dict[str, Any]:
    return _event(TOOL_CALL_ARGS, toolCallId=tool_call_id, delta=delta)


def tool_call_end(tool_call_id: str) -> Dict[str, Any]:
    return _event(TOOL_CALL_END, toolCallId=tool_call_id)


def tool_call_result(message_id: str, tool_call_id: str, content: str,
                     role: str = ROLE_TOOL) -> Dict[str, Any]:
    return _event(TOOL_CALL_RESULT, messageId=message_id,
                  toolCallId=tool_call_id, content=content, role=role)


# ---------------------------------------------------------------------------
# State events
# ---------------------------------------------------------------------------
def state_snapshot(snapshot: Any) -> Dict[str, Any]:
    return _event(STATE_SNAPSHOT, snapshot=snapshot)


def state_delta(delta: List[Dict[str, Any]]) -> Dict[str, Any]:
    """`delta` is a JSON Patch (RFC 6902) operation list."""
    return _event(STATE_DELTA, delta=delta)


def messages_snapshot(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    return _event(MESSAGES_SNAPSHOT, messages=messages)


def custom(name: str, value: Any) -> Dict[str, Any]:
    return _event(CUSTOM, name=name, value=value)


# ---------------------------------------------------------------------------
# SSE encoding
# ---------------------------------------------------------------------------
def encode(event: Dict[str, Any]) -> str:
    """Serialise one AG-UI event to a single SSE message."""
    return f"data: {json.dumps(event, ensure_ascii=False, separators=(',', ':'))}\n\n"


def encode_stream(events: Iterator[Dict[str, Any]]) -> Iterator[str]:
    """Serialise an iterable of events to SSE frames."""
    for event in events:
        yield encode(event)


# ---------------------------------------------------------------------------
# RunAgentInput — the single request body a client POSTs to start a run
# ---------------------------------------------------------------------------
@dataclass
class RunAgentInput:
    thread_id: str
    run_id: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    state: Dict[str, Any] = field(default_factory=dict)
    tools: List[Dict[str, Any]] = field(default_factory=list)
    context: List[Dict[str, Any]] = field(default_factory=list)
    forwarded_props: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "RunAgentInput":
        raw = raw or {}
        return cls(
            thread_id=str(raw.get("threadId") or new_id("thread")),
            run_id=str(raw.get("runId") or new_id("run")),
            messages=list(raw.get("messages") or []),
            state=dict(raw.get("state") or {}),
            tools=list(raw.get("tools") or []),
            context=list(raw.get("context") or []),
            forwarded_props=dict(raw.get("forwardedProps") or raw.get("forwarded_props") or {}),
        )

    def last_user_text(self) -> str:
        """Return the content of the most recent user message."""
        for msg in reversed(self.messages):
            if msg.get("role") == ROLE_USER:
                content = msg.get("content")
                if isinstance(content, str):
                    return content
                # Some clients send structured content parts.
                if isinstance(content, list):
                    return " ".join(
                        part.get("text", "") for part in content
                        if isinstance(part, dict)
                    ).strip()
                return str(content or "")
        return ""

    def to_model_messages(self) -> List[Dict[str, Any]]:
        """Project AG-UI messages onto OpenAI chat-completions messages."""
        out: List[Dict[str, Any]] = []
        for msg in self.messages:
            role = msg.get("role")
            if role not in (ROLE_SYSTEM, ROLE_DEVELOPER, ROLE_USER,
                            ROLE_ASSISTANT, ROLE_TOOL):
                continue
            entry: Dict[str, Any] = {"role": "system" if role == ROLE_DEVELOPER else role,
                                     "content": msg.get("content") or ""}
            if role == ROLE_ASSISTANT and msg.get("toolCalls"):
                entry["tool_calls"] = [
                    {
                        "id": tc.get("id"),
                        "type": "function",
                        "function": {
                            "name": tc.get("function", {}).get("name"),
                            "arguments": tc.get("function", {}).get("arguments", "{}"),
                        },
                    }
                    for tc in msg["toolCalls"]
                ]
            if role == ROLE_TOOL and msg.get("toolCallId"):
                entry["tool_call_id"] = msg["toolCallId"]
            out.append(entry)
        return out
