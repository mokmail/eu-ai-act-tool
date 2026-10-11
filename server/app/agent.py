"""
The AG-UI agent loop.

Consumes normalised chunks from an injected transport (see ``llm.py``), executes
the tool calls the model asks for, feeds the results back, and repeats until the
model answers without a tool — emitting every step as an AG-UI event so the UI
can show the work and a test can assert the exact sequence.

Design rules (deliberately followed):

* **Transport-agnostic.** ``run_agent`` takes any object with
  ``stream(messages, tools)``; the HTTP/SSE adaptation lives in ``main.py``.
  The whole loop is therefore verifiable with a scripted transport.
* **Feed the assistant turn back verbatim**, including its ``tool_calls``,
  *before* the tool results — otherwise the next request has no call for the
  result to answer and providers reject or ignore it.
* **Reassemble streamed tool-call fragments** keyed by ``index``; unparsable
  arguments fall back to ``{}`` rather than raising.
* **Bound the loop** with ``max_steps``.

Event order per tool invocation (one ``Step`` brackets the whole call)::

    STEP_STARTED → TOOL_CALL_START → TOOL_CALL_ARGS → TOOL_CALL_END
                 → TOOL_CALL_RESULT → STEP_FINISHED
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterator, List, Optional, Protocol, Tuple

from . import agui
from .tools import TOOL_NAMES, TOOL_SCHEMAS, ToolError, execute

# Only actual provisions belong in the "legal basis" footer — a tool's own
# bookkeeping ref (e.g. "checklist: provider / high_risk") is not a citation.
_LEGAL_REF = re.compile(r"^(Article|Recital|Annex|Chapter)\b")

SYSTEM_PROMPT = (
    "You are an expert assistant on the EU AI Act (Regulation (EU) 2024/1689), "
    "operating as the reasoning layer of a legal-navigation tool.\n\n"
    "You have tools that read the official text of the Act and the curated "
    "analytical dataset. Rules:\n"
    "1. ALWAYS ground your answer in tool output. Never answer from memory and "
    "never invent a provision, article number or penalty.\n"
    "2. Cite the specific Article, Recital or Annex you relied on, inline, e.g. "
    "'Article 5(1)(a)' or 'Annex III, point 4'.\n"
    "3. Prefer the precise tool: use get_article / get_recital / get_annex for a "
    "known reference; search_act to locate a term; semantic_search for conceptual "
    "questions; the structured tools for tiers, actors, checklists, timelines, "
    "penalties, definitions and governance.\n"
    "4. If tool output does not answer the question, say so plainly instead of "
    "guessing.\n"
    "5. Be concise and structured. Use short paragraphs and bullet lists."
)

MAX_STEPS = 6


class Transport(Protocol):
    """Minimal contract the loop needs from a chat backend."""

    def stream(self, messages: List[Dict[str, Any]],
               tools: Optional[List[Dict[str, Any]]] = None) -> Iterator[Dict[str, Any]]:
        ...


def _parse_args(raw: str) -> Dict[str, Any]:
    """Parse streamed tool arguments; fall back to {} so a bad call can't kill the turn."""
    if not raw or not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {"value": parsed}
    except json.JSONDecodeError:
        return {}


def _collect_turn(transport: Transport, messages: List[Dict[str, Any]],
                  tools: List[Dict[str, Any]]) -> Iterator[Tuple[str, Any]]:
    """
    Stream one assistant turn.

    Yields ``("text", delta)`` for live text, ``("end", None)`` when a text
    message closes, and finally ``("calls", [ ... ])`` with the reassembled tool
    calls for the turn (fragments joined per ``index``).
    """
    pending: Dict[int, Dict[str, Any]] = {}
    order: List[int] = []
    message_open = False

    for chunk in transport.stream(messages, tools):
        kind = chunk.get("type")
        if kind == "text":
            delta = chunk.get("delta") or ""
            if delta:
                yield ("text", delta)
        elif kind == "tool_call":
            idx = int(chunk.get("index") or 0)
            if idx not in pending:
                pending[idx] = {"id": None, "name": None, "args": ""}
                order.append(idx)
            slot = pending[idx]
            if chunk.get("id"):
                slot["id"] = chunk["id"]
            if chunk.get("name"):
                slot["name"] = chunk["name"]
            if chunk.get("args_delta"):
                slot["args"] += chunk["args_delta"]

    yield ("calls", [pending[i] for i in order])


def run_agent(
    inp: agui.RunAgentInput,
    transport: Transport,
    *,
    tools: List[Dict[str, Any]] = TOOL_SCHEMAS,
    system_prompt: str = SYSTEM_PROMPT,
    max_steps: int = MAX_STEPS,
) -> Iterator[Dict[str, Any]]:
    """Drive one run to completion, yielding AG-UI events."""
    thread_id, run_id = inp.thread_id, inp.run_id
    yield agui.run_started(thread_id, run_id, input=inp.forwarded_props or None)
    yield agui.state_snapshot(
        {
            "threadId": thread_id,
            "model": getattr(transport, "model", "unknown"),
            "tools": TOOL_NAMES,
            "status": "running",
        }
    )

    messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
    messages.extend(inp.to_model_messages())
    sources: List[str] = []

    try:
        for _step in range(max_steps):
            text_parts: List[str] = []
            calls: List[Dict[str, Any]] = []
            message_id: Optional[str] = None
            message_open = False

            for kind, payload in _collect_turn(transport, messages, tools):
                if kind == "text":
                    if not message_open:
                        message_id = agui.new_id("msg")
                        message_open = True
                        yield agui.text_message_start(message_id)
                    text_parts.append(payload)
                    yield agui.text_message_content(message_id or "", payload)
                elif kind == "calls":
                    calls = payload

            if message_open and message_id:
                yield agui.text_message_end(message_id)

            # No tool calls -> the model answered. Done.
            if not calls:
                break

            # Record the assistant turn verbatim (with its calls) before results.
            assistant_calls = [
                {
                    "id": c["id"] or agui.new_id("call"),
                    "type": "function",
                    "function": {"name": c["name"] or "unknown",
                                 "arguments": c["args"] or "{}"},
                }
                for c in calls
            ]
            messages.append(
                {"role": "assistant", "content": "".join(text_parts),
                 "tool_calls": assistant_calls}
            )

            for call, assistant_call in zip(calls, assistant_calls):
                tool_call_id = assistant_call["id"]
                name = assistant_call["function"]["name"]

                yield agui.step_started(name)
                yield agui.tool_call_start(tool_call_id, name)
                yield agui.tool_call_args(tool_call_id, call["args"] or "{}")
                yield agui.tool_call_end(tool_call_id)

                try:
                    result = execute(name, _parse_args(call["args"]))
                except ToolError as exc:
                    result = {"error": str(exc)}
                except Exception as exc:  # noqa: BLE001 - a tool bug must not kill the run
                    result = {"error": f"{type(exc).__name__}: {exc}"}

                ref = result.get("ref")
                if "error" not in result and ref:
                    candidates = ref if isinstance(ref, list) else [ref]
                    for candidate in candidates:
                        for part in str(candidate).split(","):
                            part = part.strip()
                            if _LEGAL_REF.match(part) and part not in sources:
                                sources.append(part)

                content = json.dumps(result, ensure_ascii=False)
                yield agui.tool_call_result(agui.new_id("msg"), tool_call_id, content)
                yield agui.step_finished(name)

                messages.append({"role": "tool", "tool_call_id": tool_call_id,
                                 "content": content})
        else:
            # Loop cap reached with the model still calling tools.
            message_id = agui.new_id("msg")
            yield agui.text_message_start(message_id)
            yield agui.text_message_content(
                message_id,
                f"\n\n[Reached the step limit ({max_steps} model/tool rounds) before a "
                "final answer. Ask a narrower follow-up to continue.]",
            )
            yield agui.text_message_end(message_id)

    except Exception as exc:  # noqa: BLE001 - every run ends with a terminal event
        yield agui.run_error(f"{type(exc).__name__}: {exc}", code="agent_error")
        return

    if sources:
        yield agui.custom("sources", sources)
    yield agui.state_delta([{"op": "replace", "path": "/status", "value": "finished"}])
    yield agui.run_finished(thread_id, run_id, outcome={"type": "success"})
