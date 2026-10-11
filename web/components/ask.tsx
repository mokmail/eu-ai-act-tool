"use client";

import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import type { AssistantTurn, ToolCallView, Turn } from "@/lib/agui";
import { Badge, Label, Spinner } from "@/components/shell";

const SUGGESTIONS = [
  "What AI practices are prohibited under Article 5?",
  "Is a CV-screening tool high-risk, and what must its provider do?",
  "Compare the obligations of a provider and a deployer of a high-risk system.",
  "What are the penalties for breaching the transparency rules?",
  "When does each chapter of the Act start to apply?",
];

/* ---------------------------------------------------------------------------
   A tool call, rendered as the work the agent did.
--------------------------------------------------------------------------- */
function ToolCallCard({ call }: { call: ToolCallView }) {
  let prettyArgs = call.args;
  try {
    prettyArgs = JSON.stringify(JSON.parse(call.args || "{}"), null, 2);
  } catch {
    /* keep raw */
  }

  let prettyResult = call.result ?? "";
  try {
    prettyResult = JSON.stringify(JSON.parse(call.result ?? ""), null, 2);
  } catch {
    /* keep raw */
  }

  const state =
    call.status === "streaming"
      ? "calling"
      : call.status === "running"
        ? "running"
        : call.error
          ? "error"
          : "done";

  return (
    <details className="rise group border border-line-dim bg-bg-void">
      <summary className="flex cursor-pointer list-none items-center gap-3 px-3 py-2 [&::-webkit-details-marker]:hidden">
        <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-text-faint">
          tool
        </span>
        <span className="font-mono text-[11px] text-text-ghost">{call.name}</span>
        {call.ref ? (
          <span className="truncate font-display text-[11px] text-text-faint">{call.ref}</span>
        ) : null}
        <span className="ml-auto flex items-center gap-2">
          {call.status === "streaming" || call.status === "running" ? (
            <span className="pulse-line inline-block h-[6px] w-[6px] bg-text-ghost" />
          ) : (
            <span className="inline-block h-[6px] w-[6px] bg-text-faint" />
          )}
          <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-text-faint">
            {state}
          </span>
          <span className="font-mono text-[10px] text-text-faint opacity-0 transition-opacity group-hover:opacity-100">
            ⌄
          </span>
        </span>
      </summary>
      <div className="border-t border-line-dim px-3 py-3">
        <Label faint>arguments</Label>
        <pre className="mt-2 max-h-48 overflow-auto bg-bg-panel-hi px-3 py-2 font-mono text-[11px] leading-relaxed text-text-dim">
          {prettyArgs || "{}"}
        </pre>
        {call.result ? (
          <>
            <Label faint className="mt-3 block">
              result
            </Label>
            <pre className="mt-2 max-h-72 overflow-auto bg-bg-panel-hi px-3 py-2 font-mono text-[11px] leading-relaxed text-text-dim">
              {prettyResult}
            </pre>
          </>
        ) : null}
      </div>
    </details>
  );
}

function AssistantBlock({ turn }: { turn: AssistantTurn }) {
  return (
    <div className="rise flex flex-col gap-3">
      <div className="flex items-center gap-3">
        <Label faint>agent</Label>
        {turn.step ? (
          <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-text-faint">
            {turn.step}…
          </span>
        ) : null}
      </div>

      {turn.tools.length > 0 ? (
        <div className="flex flex-col gap-2">
          {turn.tools.map((call) => (
            <ToolCallCard key={call.id} call={call} />
          ))}
        </div>
      ) : null}

      {turn.content ? (
        <div className={`prose-act ${turn.streaming ? "caret" : ""}`}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{turn.content}</ReactMarkdown>
        </div>
      ) : turn.streaming && turn.tools.length === 0 ? (
        <Spinner label="thinking" />
      ) : null}
    </div>
  );
}

/* ---------------------------------------------------------------------------
   The view
--------------------------------------------------------------------------- */
export function AskView({
  turns,
  running,
  sources,
  onSend,
  onStop,
}: {
  turns: Turn[];
  running: boolean;
  sources: string[];
  onSend: (text: string) => void;
  onStop: () => void;
}) {
  const [draft, setDraft] = useState("");
  const scroller = useRef<HTMLDivElement | null>(null);
  const stick = useRef(true);

  useEffect(() => {
    const el = scroller.current;
    if (!el || !stick.current) return;
    el.scrollTop = el.scrollHeight;
  }, [turns]);

  const onScroll = () => {
    const el = scroller.current;
    if (!el) return;
    stick.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
  };

  const submit = () => {
    const text = draft.trim();
    if (!text || running) return;
    stick.current = true;
    setDraft("");
    onSend(text);
  };

  return (
    <div className="flex h-full flex-col">
      <div
        ref={scroller}
        onScroll={onScroll}
        className="flex-1 overflow-y-auto px-5 py-8 md:px-8"
      >
        <div className="mx-auto flex max-w-[74ch] flex-col gap-8">
          {turns.length === 0 ? (
            <div className="flex flex-col gap-6">
              <div className="flex flex-col gap-3">
                <Label faint>ask the act</Label>
                <h2 className="font-display text-[clamp(1.5rem,2.6vw,2.15rem)] font-light leading-[1.15] tracking-[-0.02em] text-text-ghost">
                  Every answer cites the article it stands on.
                </h2>
                <p className="font-display text-[15px] leading-relaxed text-text-dim">
                  The agent reads the official EUR-Lex text and the curated dataset
                  through its tools, then streams its work back over the AG-UI protocol —
                  you see each call and its result as it happens.
                </p>
              </div>
              <div className="flex flex-col divide-y divide-line-dim border-y border-line-dim">
                {SUGGESTIONS.map((text) => (
                  <button
                    key={text}
                    onClick={() => onSend(text)}
                    className="group flex items-baseline gap-3 py-3 text-left transition-opacity hover:opacity-60"
                  >
                    <span className="font-mono text-[10px] text-text-faint">→</span>
                    <span className="font-display text-[14px] leading-relaxed text-text-dim">
                      {text}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          {turns.map((turn) => {
            if (turn.kind === "user") {
              return (
                <div key={turn.id} className="rise flex flex-col gap-2">
                  <Label faint>you</Label>
                  <p className="border-l border-line-hi pl-4 font-display text-[15px] leading-relaxed text-text-ghost">
                    {turn.content}
                  </p>
                </div>
              );
            }
            if (turn.kind === "error") {
              return (
                <div key={turn.id} className="rise flex flex-col gap-2">
                  <Label faint>error</Label>
                  <p className="border-l border-line-hi pl-4 font-mono text-[12px] leading-relaxed text-text-dim">
                    {turn.message}
                  </p>
                </div>
              );
            }
            return <AssistantBlock key={turn.id} turn={turn} />;
          })}

          {sources.length > 0 ? (
            <div className="rise flex flex-wrap items-center gap-2 border-t border-line-dim pt-4">
              <Label faint>legal basis</Label>
              {sources.map((s) => (
                <Badge key={s} tone="outline">
                  {s}
                </Badge>
              ))}
            </div>
          ) : null}
        </div>
      </div>

      <div className="border-t border-line-dim bg-bg-void">
        <div className="mx-auto flex max-w-[74ch] flex-col gap-2 px-5 py-4 md:px-8">
          <div className="flex items-end gap-3">
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  submit();
                }
              }}
              rows={1}
              placeholder="Ask about a provision, an obligation, a risk tier…"
              className="max-h-40 min-h-[42px] flex-1 resize-none border border-line-dim bg-bg-panel px-3 py-3 font-display text-[14px] leading-relaxed text-text-ghost outline-none transition-colors placeholder:text-text-faint focus:border-line-hi"
            />
            {running ? (
              <button
                onClick={onStop}
                className="border border-line-hi px-4 py-[11px] font-mono text-[10px] uppercase tracking-[0.24em] text-text-ghost transition-opacity hover:opacity-60"
              >
                stop
              </button>
            ) : (
              <button
                onClick={submit}
                disabled={!draft.trim()}
                className="border border-text-ghost bg-text-ghost px-4 py-[11px] font-mono text-[10px] uppercase tracking-[0.24em] text-bg-void transition-opacity hover:opacity-70 disabled:cursor-not-allowed disabled:border-line-dim disabled:bg-transparent disabled:text-text-faint"
              >
                ask
              </button>
            )}
          </div>
          {/* Which model answered is deliberately not shown: on your own
              infrastructure it is an implementation detail. It lives in Settings. */}
          <div className="flex items-center justify-between">
            <Label faint>enter to send · shift+enter for a new line</Label>
          </div>
        </div>
      </div>
    </div>
  );
}
