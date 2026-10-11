"use client";

/**
 * AG-UI client for the EU AI Act navigator.
 *
 * Wraps `@ag-ui/client`'s `HttpAgent` in a React hook. The SDK owns the protocol
 * (it parses the SSE stream, validates events and applies them to its own
 * message/state stores); we subscribe to the typed event hooks and fold them
 * into a flat transcript the UI can render — text deltas, tool-call cards, the
 * run lifecycle and an optional raw event log.
 */

import { useCallback, useRef, useState } from "react";
import { HttpAgent } from "@ag-ui/client";
import type { BaseEvent } from "@ag-ui/client";

export const AGENT_URL =
  process.env.NEXT_PUBLIC_AGENT_URL ?? "http://127.0.0.1:8000/agent";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

export type ToolCallView = {
  id: string;
  name: string;
  args: string;
  result?: string;
  /** The `ref` the server reported, e.g. "Article 5". */
  ref?: string;
  error?: boolean;
  status: "streaming" | "running" | "done";
};

export type AssistantTurn = {
  kind: "assistant";
  id: string;
  content: string;
  tools: ToolCallView[];
  streaming: boolean;
  step?: string;
};

export type Turn =
  | { kind: "user"; id: string; content: string }
  | AssistantTurn
  | { kind: "error"; id: string; message: string };

let counter = 0;
const uid = (prefix: string) => `${prefix}_${Date.now().toString(36)}_${counter++}`;

export function useAgui() {
  const agentRef = useRef<HttpAgent | null>(null);
  const turnIdRef = useRef<string | null>(null);

  const [turns, setTurns] = useState<Turn[]>([]);
  const [running, setRunning] = useState(false);
  const [model, setModel] = useState<string | null>(null);
  const [sources, setSources] = useState<string[]>([]);
  const [events, setEvents] = useState<BaseEvent[]>([]);

  /** Create (or re-create) the agent. Called once, lazily. */
  const getAgent = useCallback(() => {
    if (agentRef.current) return agentRef.current;
    const agent = new HttpAgent({ url: AGENT_URL, threadId: uid("thread") });

    const mutateAssistant = (
      fn: (turn: AssistantTurn) => AssistantTurn
    ) => {
      const id = turnIdRef.current;
      if (!id) return;
      setTurns((prev) => {
        const idx = prev.findIndex((t) => t.kind === "assistant" && t.id === id);
        if (idx === -1) {
          return [
            ...prev,
            fn({ kind: "assistant", id, content: "", tools: [], streaming: true }),
          ];
        }
        const next = [...prev];
        next[idx] = fn(next[idx] as AssistantTurn);
        return next;
      });
    };

    agent.subscribe({
      onEvent: ({ event }) => {
        setEvents((prev) => [...prev.slice(-119), event]);
      },

      onRunStartedEvent: ({ event }) => {
        turnIdRef.current = `assistant:${event.runId}`;
      },

      onStateSnapshotEvent: ({ event }) => {
        const snap = event.snapshot as { model?: string } | undefined;
        if (snap?.model) setModel(snap.model);
      },

      onTextMessageStartEvent: () => {
        mutateAssistant((t) => ({ ...t, streaming: true }));
      },

      onTextMessageContentEvent: ({ event }) => {
        mutateAssistant((t) => ({ ...t, content: t.content + event.delta }));
      },

      onTextMessageEndEvent: () => {
        mutateAssistant((t) => ({ ...t }));
      },

      onToolCallStartEvent: ({ event }) => {
        mutateAssistant((t) => ({
          ...t,
          tools: [
            ...t.tools,
            {
              id: event.toolCallId,
              name: event.toolCallName,
              args: "",
              status: "streaming",
            },
          ],
        }));
      },

      onToolCallArgsEvent: ({ event }) => {
        mutateAssistant((t) => ({
          ...t,
          tools: t.tools.map((tool) =>
            tool.id === event.toolCallId
              ? { ...tool, args: tool.args + event.delta }
              : tool
          ),
        }));
      },

      onToolCallEndEvent: ({ event }) => {
        mutateAssistant((t) => ({
          ...t,
          tools: t.tools.map((tool) =>
            tool.id === event.toolCallId ? { ...tool, status: "running" } : tool
          ),
        }));
      },

      onToolCallResultEvent: ({ event }) => {
        const raw =
          typeof event.content === "string"
            ? event.content
            : JSON.stringify(event.content);
        let ref: string | undefined;
        let error = false;
        try {
          const parsed = JSON.parse(raw);
          ref = typeof parsed?.ref === "string" ? parsed.ref : undefined;
          error = Boolean(parsed?.error);
        } catch {
          /* result was not JSON — show it verbatim */
        }
        mutateAssistant((t) => ({
          ...t,
          tools: t.tools.map(
            (tool): ToolCallView =>
              tool.id === event.toolCallId
                ? { ...tool, result: raw, ref, error, status: "done" }
                : tool
          ),
        }));
      },

      onStepStartedEvent: ({ event }) => {
        mutateAssistant((t) => ({ ...t, step: event.stepName }));
      },

      onStepFinishedEvent: () => {
        mutateAssistant((t) => ({ ...t, step: undefined }));
      },

      onCustomEvent: ({ event }) => {
        if (event.name === "sources" && Array.isArray(event.value)) {
          setSources(event.value as string[]);
        }
      },

      onRunErrorEvent: ({ event }) => {
        setTurns((prev) => [
          ...prev,
          { kind: "error", id: uid("err"), message: event.message },
        ]);
        mutateAssistant((t) => ({ ...t, streaming: false }));
      },

      onRunFailed: ({ error }) => {
        setTurns((prev) => [
          ...prev,
          { kind: "error", id: uid("err"), message: error.message },
        ]);
        mutateAssistant((t) => ({ ...t, streaming: false }));
      },

      onRunFinalized: () => {
        mutateAssistant((t) => ({ ...t, streaming: false, step: undefined }));
        setRunning(false);
      },
    });

    agentRef.current = agent;
    return agent;
  }, []);

  const send = useCallback(
    async (text: string) => {
      const question = text.trim();
      if (!question || running) return;

      const agent = getAgent();
      // Seed the agent's message store: the SDK builds RunAgentInput from it.
      agent.messages = [
        ...agent.messages,
        { id: uid("msg"), role: "user", content: question },
      ];

      setTurns((prev) => [...prev, { kind: "user", id: uid("u"), content: question }]);
      setSources([]);
      setRunning(true);

      try {
        await agent.runAgent({ runId: uid("run") });
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        setTurns((prev) => [...prev, { kind: "error", id: uid("err"), message }]);
      } finally {
        setRunning(false);
        mutateAssistantSafe();
      }

      function mutateAssistantSafe() {
        const id = turnIdRef.current;
        if (!id) return;
        setTurns((prev) =>
          prev.map((t) =>
            t.kind === "assistant" && t.id === id ? { ...t, streaming: false } : t
          )
        );
      }
    },
    [getAgent, running]
  );

  const stop = useCallback(() => {
    agentRef.current?.abortRun();
    setRunning(false);
  }, []);

  const reset = useCallback(() => {
    agentRef.current?.abortRun();
    agentRef.current = null;
    turnIdRef.current = null;
    setTurns([]);
    setSources([]);
    setEvents([]);
    setRunning(false);
    setModel(null);
  }, []);

  return { turns, running, model, sources, events, send, stop, reset };
}
