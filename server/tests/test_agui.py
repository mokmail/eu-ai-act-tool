"""AG-UI wire layer: event constructors, SSE encoding, RunAgentInput parsing."""
import json

from app import agui


def _parse_sse(frame: str) -> dict:
    assert frame.startswith("data: ")
    assert frame.endswith("\n\n")
    return json.loads(frame[len("data: "):].strip())


def test_every_event_carries_type_and_timestamp():
    events = [
        agui.run_started("t1", "r1"),
        agui.run_finished("t1", "r1"),
        agui.run_error("boom"),
        agui.step_started("s"),
        agui.step_finished("s"),
        agui.text_message_start("m1"),
        agui.text_message_content("m1", "x"),
        agui.text_message_end("m1"),
        agui.tool_call_start("c1", "search_act"),
        agui.tool_call_args("c1", "{}"),
        agui.tool_call_end("c1"),
        agui.tool_call_result("m2", "c1", "ok"),
        agui.state_snapshot({}),
        agui.state_delta([]),
        agui.messages_snapshot([]),
        agui.custom("sources", []),
    ]
    for evt in events:
        assert isinstance(evt["type"], str) and evt["type"]
        assert isinstance(evt["timestamp"], int)


def test_encode_is_a_single_sse_frame():
    frame = agui.encode(agui.text_message_content("m1", "hello"))
    evt = _parse_sse(frame)
    assert evt["type"] == agui.TEXT_MESSAGE_CONTENT
    assert evt["messageId"] == "m1"
    assert evt["delta"] == "hello"


def test_encode_stream_frames_in_order():
    frames = list(agui.encode_stream(iter([
        agui.run_started("t", "r"),
        agui.run_finished("t", "r"),
    ])))
    assert len(frames) == 2
    assert _parse_sse(frames[0])["type"] == agui.RUN_STARTED
    assert _parse_sse(frames[1])["type"] == agui.RUN_FINISHED


def test_run_started_carries_thread_and_run_ids():
    evt = agui.run_started("thread-1", "run-1")
    assert evt["threadId"] == "thread-1"
    assert evt["runId"] == "run-1"


def test_tool_call_result_is_role_tool():
    evt = agui.tool_call_result("m1", "c1", "content")
    assert evt["role"] == "tool"
    assert evt["toolCallId"] == "c1"
    assert evt["content"] == "content"


def test_state_delta_is_a_json_patch_list():
    evt = agui.state_delta([{"op": "replace", "path": "/a", "value": 1}])
    assert isinstance(evt["delta"], list)
    assert evt["delta"][0]["op"] == "replace"


def test_run_agent_input_generates_ids_when_absent():
    inp = agui.RunAgentInput.from_dict({"messages": []})
    assert inp.thread_id.startswith("thread_")
    assert inp.run_id.startswith("run_")


def test_last_user_text_returns_most_recent_user_message():
    inp = agui.RunAgentInput.from_dict({
        "messages": [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "reply"},
            {"role": "user", "content": "second"},
        ]
    })
    assert inp.last_user_text() == "second"


def test_last_user_text_handles_structured_content_parts():
    inp = agui.RunAgentInput.from_dict({
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]}
        ]
    })
    assert inp.last_user_text() == "a b"


def test_to_model_messages_projects_tool_calls_and_results():
    inp = agui.RunAgentInput.from_dict({
        "messages": [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "",
             "toolCalls": [{"id": "c1", "function": {"name": "get_article",
                                                    "arguments": '{"number":"5"}'}}]},
            {"role": "tool", "toolCallId": "c1", "content": "{}"},
        ]
    })
    msgs = inp.to_model_messages()
    assert msgs[0] == {"role": "user", "content": "hi"}
    assert msgs[1]["tool_calls"][0]["function"]["name"] == "get_article"
    assert msgs[1]["tool_calls"][0]["id"] == "c1"
    assert msgs[2]["tool_call_id"] == "c1"
    assert msgs[2]["role"] == "tool"


def test_to_model_messages_maps_developer_role_to_system():
    inp = agui.RunAgentInput.from_dict({
        "messages": [{"role": "developer", "content": "be terse"}]
    })
    assert inp.to_model_messages()[0]["role"] == "system"


def test_custom_event_shape():
    evt = agui.custom("sources", ["Article 5"])
    assert evt["name"] == "sources"
    assert evt["value"] == ["Article 5"]
