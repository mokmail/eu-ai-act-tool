"""
Agent loop verified against a scripted transport — no model, no network, no server.

Covers: the exact event sequence, streamed tool-call fragment reassembly, malformed
arguments, an unknown tool, the step cap, a raising transport, and the ordering
rule that the assistant turn (with its ``tool_calls``) is fed back before results.
"""
from __future__ import annotations

import json
from typing import Any, Dict, Iterator, List, Optional

import pytest

from app import agui, agent


class ScriptedTransport:
    """Replays a fixed list of turns, recording the messages it is asked to send."""

    model = "scripted-test"

    def __init__(self, turns: List[List[Dict[str, Any]]]):
        self._turns = list(turns)
        self.seen_messages: List[List[Dict[str, Any]]] = []

    def stream(self, messages, tools=None) -> Iterator[Dict[str, Any]]:
        self.seen_messages.append([dict(m) for m in messages])
        if not self._turns:
            yield {"type": "finish", "reason": "stop"}
            return
        for chunk in self._turns.pop(0):
            yield chunk


class BoomTransport:
    model = "boom"

    def stream(self, messages, tools=None):
        raise RuntimeError("provider exploded")


def inp(text: str = "What does Article 5 prohibit?") -> agui.RunAgentInput:
    return agui.RunAgentInput.from_dict({
        "threadId": "t1", "runId": "r1",
        "messages": [{"role": "user", "content": text}],
    })


def types(events) -> List[str]:
    return [e["type"] for e in events]


def run(transport, **kwargs) -> List[Dict[str, Any]]:
    return list(agent.run_agent(inp(), transport, **kwargs))


def text_of(events) -> str:
    return "".join(e["delta"] for e in events if e["type"] == agui.TEXT_MESSAGE_CONTENT)


# -- 1. the event sequence for a plain answer -------------------------------
def test_plain_answer_event_sequence():
    transport = ScriptedTransport([[
        {"type": "text", "delta": "Article 5 "},
        {"type": "text", "delta": "bans certain practices."},
        {"type": "finish", "reason": "stop"},
    ]])
    events = run(transport)
    assert types(events) == [
        agui.RUN_STARTED,
        agui.STATE_SNAPSHOT,
        agui.TEXT_MESSAGE_START,
        agui.TEXT_MESSAGE_CONTENT,
        agui.TEXT_MESSAGE_CONTENT,
        agui.TEXT_MESSAGE_END,
        agui.STATE_DELTA,
        agui.RUN_FINISHED,
    ]
    assert text_of(events) == "Article 5 bans certain practices."
    # every text event shares one messageId
    ids = {e["messageId"] for e in events if "messageId" in e and e["type"] != agui.TOOL_CALL_RESULT}
    assert len(ids) == 1


def test_run_bracketed_by_started_and_finished_with_matching_ids():
    transport = ScriptedTransport([[{"type": "finish", "reason": "stop"}]])
    events = run(transport)
    assert events[0]["type"] == agui.RUN_STARTED
    assert events[-1]["type"] == agui.RUN_FINISHED
    assert events[0]["runId"] == events[-1]["runId"] == "r1"


# -- 2. tool call, then answer ----------------------------------------------
def test_tool_call_executes_and_feeds_result_back():
    transport = ScriptedTransport([
        [
            {"type": "tool_call", "index": 0, "id": "call_1",
             "name": "get_article", "args_delta": '{"num'},
            {"type": "tool_call", "index": 0, "args_delta": 'ber":"5"}'},
            {"type": "finish", "reason": "tool_calls"},
        ],
        [{"type": "text", "delta": "Article 5 prohibits ..."},
         {"type": "finish", "reason": "stop"}],
    ])
    events = run(transport)
    seq = types(events)

    # the full tool lifecycle is present, in order
    assert seq.index(agui.TOOL_CALL_START) < seq.index(agui.TOOL_CALL_ARGS)
    assert seq.index(agui.TOOL_CALL_ARGS) < seq.index(agui.TOOL_CALL_END)
    assert seq.index(agui.TOOL_CALL_END) < seq.index(agui.TOOL_CALL_RESULT)
    assert seq.index(agui.STEP_STARTED) < seq.index(agui.TOOL_CALL_START)
    assert seq.index(agui.TOOL_CALL_RESULT) < seq.index(agui.STEP_FINISHED)

    # fragment reassembly: both arg fragments joined, then the tool really ran
    result = next(e for e in events if e["type"] == agui.TOOL_CALL_RESULT)
    payload = json.loads(result["content"])
    assert payload["ref"] == "Article 5"
    assert "prohibited" in payload["text"].lower()

    # sources custom event carries the citation
    sources = next(e for e in events if e["type"] == agui.CUSTOM)
    assert sources["name"] == "sources"
    assert "Article 5" in sources["value"]


def test_assistant_turn_is_fed_back_with_tool_calls_before_results():
    transport = ScriptedTransport([
        [{"type": "tool_call", "index": 0, "id": "call_1",
          "name": "get_article", "args_delta": '{"number":"5"}'},
         {"type": "finish", "reason": "tool_calls"}],
        [{"type": "text", "delta": "done"}, {"type": "finish", "reason": "stop"}],
    ])
    run(transport)

    second_request = transport.seen_messages[1]
    roles = [m["role"] for m in second_request]
    assistant_idx = roles.index("assistant")
    tool_idx = roles.index("tool")
    assert assistant_idx < tool_idx, "assistant call must precede its tool result"
    assistant_msg = second_request[assistant_idx]
    assert assistant_msg["tool_calls"][0]["id"] == "call_1"
    assert assistant_msg["tool_calls"][0]["function"]["name"] == "get_article"
    assert json.loads(assistant_msg["tool_calls"][0]["function"]["arguments"]) == {"number": "5"}
    assert second_request[tool_idx]["tool_call_id"] == "call_1"


def test_two_tool_calls_in_one_turn_are_tracked_separately():
    transport = ScriptedTransport([
        [
            {"type": "tool_call", "index": 0, "id": "c0", "name": "get_article",
             "args_delta": '{"number":"5"}'},
            {"type": "tool_call", "index": 1, "id": "c1", "name": "citation",
             "args_delta": "{}"},
            {"type": "finish", "reason": "tool_calls"},
        ],
        [{"type": "text", "delta": "ok"}, {"type": "finish", "reason": "stop"}],
    ])
    events = run(transport)
    starts = [e for e in events if e["type"] == agui.TOOL_CALL_START]
    results = [e for e in events if e["type"] == agui.TOOL_CALL_RESULT]
    assert [s["toolCallName"] for s in starts] == ["get_article", "citation"]
    assert {r["toolCallId"] for r in results} == {"c0", "c1"}


# -- 3. malformed / hostile tool arguments ----------------------------------
def test_malformed_tool_arguments_fall_back_to_empty_and_surface_error():
    transport = ScriptedTransport([
        [{"type": "tool_call", "index": 0, "id": "c1", "name": "search_act",
          "args_delta": "{this is not json"},
         {"type": "finish", "reason": "tool_calls"}],
        [{"type": "text", "delta": "recovered"}, {"type": "finish", "reason": "stop"}],
    ])
    events = run(transport)
    result = next(e for e in events if e["type"] == agui.TOOL_CALL_RESULT)
    assert "error" in json.loads(result["content"])
    # the run still completes
    assert events[-1]["type"] == agui.RUN_FINISHED
    assert text_of(events) == "recovered"


def test_unknown_tool_surfaces_error_without_killing_the_run():
    transport = ScriptedTransport([
        [{"type": "tool_call", "index": 0, "id": "c1", "name": "delete_everything",
          "args_delta": "{}"},
         {"type": "finish", "reason": "tool_calls"}],
        [{"type": "text", "delta": "no such tool"}, {"type": "finish", "reason": "stop"}],
    ])
    events = run(transport)
    result = next(e for e in events if e["type"] == agui.TOOL_CALL_RESULT)
    assert "Unknown tool" in json.loads(result["content"])["error"]
    assert events[-1]["type"] == agui.RUN_FINISHED


# -- 4. the step cap ---------------------------------------------------------
def test_step_cap_bounds_a_tool_only_loop():
    loop_turn = [
        {"type": "tool_call", "index": 0, "id": "c1", "name": "citation",
         "args_delta": "{}"},
        {"type": "finish", "reason": "tool_calls"},
    ]
    transport = ScriptedTransport([loop_turn, loop_turn, loop_turn, loop_turn])
    events = run(transport, max_steps=2)

    assert len([e for e in events if e["type"] == agui.TOOL_CALL_RESULT]) == 2
    assert "step limit" in text_of(events)
    assert events[-1]["type"] == agui.RUN_FINISHED


# -- 5. a raising transport --------------------------------------------------
def test_transport_failure_emits_run_error():
    events = run(BoomTransport())
    assert events[-1]["type"] == agui.RUN_ERROR
    assert "provider exploded" in events[-1]["message"]
    assert agui.RUN_ERROR in types(events)


def test_run_error_is_terminal():
    events = run(BoomTransport())
    assert agui.RUN_FINISHED not in types(events)


def test_sources_are_legal_refs_only_deduped_and_split():
    transport = ScriptedTransport([
        [
            {"type": "tool_call", "index": 0, "id": "c0", "name": "get_article",
             "args_delta": '{"number":"6"}'},
            {"type": "tool_call", "index": 1, "id": "c1", "name": "compliance_checklist",
             "args_delta": '{"actor":"provider"}'},
            {"type": "tool_call", "index": 2, "id": "c2", "name": "get_annex",
             "args_delta": '{"number":"III"}'},
            {"type": "finish", "reason": "tool_calls"},
        ],
        [{"type": "text", "delta": "done"}, {"type": "finish", "reason": "stop"}],
    ])
    events = run(transport)
    sources = next(e for e in events if e["type"] == agui.CUSTOM)["value"]
    # "Article 6, Annex III" (from classify-style tools) splits; the checklist's
    # own bookkeeping ref is dropped; duplicates collapse.
    assert sources == ["Article 6", "Annex III"]


def test_no_sources_event_when_nothing_was_cited():
    transport = ScriptedTransport([[{"type": "finish", "reason": "stop"}]])
    events = run(transport)
    assert agui.CUSTOM not in types(events)
