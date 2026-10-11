"use client";

/**
 * Classify — the Act's classification ladder, walked one question at a time,
 * plus the free-text heuristic screen as a quick second opinion.
 */

import { useCallback, useEffect, useState } from "react";

import { api, humanise } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Badge, ErrorNote, Label, Panel, Spinner, ViewHeader } from "@/components/shell";

export function ClassifyView({ onAsk }: { onAsk: (text: string) => void }) {
  const path = useApi(api.riskPath);
  const walk = useApi(api.classifyWalk);
  const quick = useApi(api.classify);

  const [answers, setAnswers] = useState<Record<string, boolean>>({});
  const [description, setDescription] = useState("");

  useEffect(() => {
    void path.run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path.run]);

  const start = useCallback(async () => {
    setAnswers({});
    await walk.run({});
  }, [walk]);

  useEffect(() => {
    void start();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const answer = async (value: boolean) => {
    const question = walk.data?.question;
    if (!question) return;
    const next = { ...answers, [question.id]: value };
    setAnswers(next);
    await walk.run(next);
  };

  const step = walk.data;

  return (
    <div className="h-full overflow-y-auto px-5 py-8 md:px-8">
      <div className="mx-auto flex max-w-[80ch] flex-col gap-8">
        <ViewHeader
          eyebrow="classify"
          title="Which risk tier applies?"
          lede="The Act classifies by intended purpose, not by technology. Answer the questions and the ladder lands you on a tier, with the obligations that follow from it."
        />

        {/* -- the ladder -- */}
        <Panel className="flex flex-col gap-6 px-5 py-5">
          {step?.trace.length ? (
            <ol className="flex flex-col gap-2 border-b border-line-dim pb-4">
              {step.trace.map((t, i) => (
                <li key={i} className="flex items-baseline gap-3">
                  <span className="font-mono text-[10px] tabular-nums text-text-faint">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <span className="font-display text-[12px] text-text-dim">{t.question}</span>
                  <span className="ml-auto font-mono text-[10px] uppercase tracking-[0.16em] text-text-ghost">
                    {t.answer}
                  </span>
                </li>
              ))}
            </ol>
          ) : null}

          {walk.loading ? <Spinner label="walking the ladder" /> : null}
          {walk.error ? <ErrorNote message={walk.error} /> : null}

          {step && !step.complete && step.question ? (
            <div className="flex flex-col gap-4">
              <Label faint>
                step {step.trace.length + 1} · {step.question.ref}
              </Label>
              <p className="max-w-[70ch] font-display text-[17px] font-light leading-snug tracking-[-0.01em] text-text-ghost">
                {step.question.question}
              </p>
              {step.question.detail ? (
                <p className="max-w-[70ch] font-display text-[13px] leading-relaxed text-text-dim">
                  {step.question.detail}
                </p>
              ) : null}
              <div className="flex gap-3">
                <button
                  onClick={() => answer(true)}
                  className="border border-text-ghost bg-text-ghost px-5 py-2 font-mono text-[10px] uppercase tracking-[0.24em] text-bg-void transition-opacity hover:opacity-70"
                >
                  yes
                </button>
                <button
                  onClick={() => answer(false)}
                  className="border border-line-hi px-5 py-2 font-mono text-[10px] uppercase tracking-[0.24em] text-text-ghost transition-opacity hover:opacity-60"
                >
                  no
                </button>
              </div>
            </div>
          ) : null}

          {step?.complete && step.detail ? (
            <div className="rise flex flex-col gap-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={step.outcome === "prohibited" ? "ghost" : "outline"}>
                  {step.detail.label}
                </Badge>
                <span className="font-mono text-[10px] text-text-faint">{step.detail.ref}</span>
                <span className="font-mono text-[10px] text-text-faint">
                  applies from {step.detail.applies_from}
                </span>
              </div>
              <p className="max-w-[70ch] font-display text-[15px] leading-relaxed text-text-ghost">
                {step.detail.summary}
              </p>
              <ul className="flex flex-col gap-2 border-t border-line-dim pt-4">
                {step.detail.actions.map((a) => (
                  <li key={a} className="flex gap-3 font-display text-[13px] leading-relaxed text-text-dim">
                    <span className="text-text-faint">—</span>
                    <span>{a}</span>
                  </li>
                ))}
              </ul>
              {step.detail.penalty ? (
                <p className="font-display text-[12px] leading-relaxed text-text-faint">
                  {step.detail.penalty}
                </p>
              ) : null}
              <div className="flex flex-wrap gap-4 border-t border-line-dim pt-4">
                <button
                  onClick={start}
                  className="font-mono text-[10px] uppercase tracking-[0.24em] text-text-dim transition-colors hover:text-text-ghost"
                >
                  start over
                </button>
                <button
                  onClick={() =>
                    onAsk(
                      `My AI system classifies as ${step.detail?.label}. Walk me through what I actually have to do, citing the articles and the deadlines.`
                    )
                  }
                  className="font-mono text-[10px] uppercase tracking-[0.24em] text-text-dim transition-colors hover:text-text-ghost"
                >
                  ask the agent what to do →
                </button>
              </div>
            </div>
          ) : null}
        </Panel>

        {/* -- quick screen -- */}
        <div className="flex flex-col gap-4 border-t border-line-dim pt-8">
          <Label faint>or describe the system</Label>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (description.trim()) void quick.run(description.trim());
            }}
            className="flex flex-col gap-3"
          >
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              placeholder="e.g. a tool that ranks job applicants from their video interviews"
              className="resize-none border border-line-dim bg-bg-panel px-3 py-3 font-display text-[14px] leading-relaxed text-text-ghost outline-none transition-colors placeholder:text-text-faint focus:border-line-hi"
            />
            <button
              type="submit"
              className="self-start border border-line-hi px-4 py-2 font-mono text-[10px] uppercase tracking-[0.24em] text-text-ghost transition-opacity hover:opacity-60"
            >
              quick screen
            </button>
          </form>

          {quick.loading ? <Spinner label="screening" /> : null}
          {quick.error ? <ErrorNote message={quick.error} /> : null}
          {quick.data ? (
            <Panel className="flex flex-col gap-3 px-5 py-4">
              <div className="flex items-center gap-3">
                <Label faint>heuristic</Label>
                <Badge tone={quick.data.likely_high_risk ? "ghost" : "outline"}>
                  {quick.data.likely_high_risk ? "high-risk" : "not high-risk"}
                </Badge>
              </div>
              <p className="font-display text-[13px] leading-relaxed text-text-ghost">{quick.data.verdict}</p>
              {quick.data.areas?.length ? (
                <ul className="flex flex-wrap gap-2">
                  {quick.data.areas.map((a) => (
                    <li key={a.area}>
                      <Badge tone="outline">
                        {a.name} · {a.ref}
                      </Badge>
                    </li>
                  ))}
                </ul>
              ) : null}
              <p className="font-display text-[11px] leading-relaxed text-text-faint">
                {quick.data.disclaimer}
              </p>
            </Panel>
          ) : null}
        </div>

        {/* keep the tier list reachable */}
        {path.data ? (
          <div className="flex flex-col gap-2 border-t border-line-dim pt-6">
            <Label faint>the six outcomes</Label>
            <ul className="flex flex-wrap gap-2">
              {Object.entries(path.data.outcomes).map(([key]) => (
                <li key={key}>
                  <Badge tone="outline">{humanise(key)}</Badge>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </div>
  );
}
