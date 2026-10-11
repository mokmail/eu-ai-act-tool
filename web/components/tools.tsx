"use client";

import { useCallback, useState } from "react";

import { ACTOR_KEYS, TIER_KEYS, api, humanise, tierLabel } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { EmptyNote, ErrorNote, Label, Spinner, ViewHeader } from "@/components/shell";

function Chips({
  options,
  value,
  onChange,
  format = humanise,
}: {
  options: readonly string[];
  value: string | null;
  onChange: (next: string) => void;
  format?: (key: string) => string;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((option) => {
        const active = option === value;
        return (
          <button
            key={option}
            onClick={() => onChange(option)}
            className={`border px-3 py-1 font-mono text-[10px] uppercase tracking-[0.18em] transition-colors ${
              active
                ? "border-text-ghost bg-text-ghost text-bg-void"
                : "border-line-dim text-text-dim hover:border-line-hi hover:text-text-ghost"
            }`}
          >
            {format(option)}
          </button>
        );
      })}
    </div>
  );
}

/* ---------------------------------------------------------------------------
   Comply — obligations and checklists per actor
--------------------------------------------------------------------------- */
export function ChecklistView({ onAsk }: { onAsk: (text: string) => void }) {
  const [actor, setActor] = useState<string>("provider");
  const [tier, setTier] = useState<string | null>("high_risk");
  const [checked, setChecked] = useState<Record<string, boolean>>({});

  const checklist = useApi(api.checklist);

  const load = useCallback(
    (nextActor: string, nextTier: string | null) => {
      setChecked({});
      void checklist.run(nextActor, nextTier ?? undefined);
    },
    [checklist]
  );

  return (
    <div className="h-full overflow-y-auto px-5 py-8 md:px-8">
      <div className="mx-auto flex max-w-[80ch] flex-col gap-8">
        <ViewHeader
          eyebrow="compliance"
          title="What you must do"
          lede="Every obligation the Act places on an actor, each carrying the article it comes from. Generate a working checklist and tick items off as you go."
        />

        <div className="flex flex-col gap-5">
          <div className="flex flex-col gap-2">
            <Label faint>actor</Label>
            <Chips
              options={ACTOR_KEYS}
              value={actor}
              onChange={(next) => {
                setActor(next);
                load(next, tier);
              }}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label faint>risk tier (optional)</Label>
            <Chips
              options={TIER_KEYS}
              value={tier}
              onChange={(next) => {
                const resolved = next === tier ? null : next;
                setTier(resolved);
                load(actor, resolved);
              }}
            />
          </div>
          <button
            onClick={() => load(actor, tier)}
            className="self-start border border-text-ghost bg-text-ghost px-4 py-2 font-mono text-[10px] uppercase tracking-[0.24em] text-bg-void transition-opacity hover:opacity-70"
          >
            generate checklist
          </button>
        </div>

        {checklist.loading ? <Spinner label="building checklist" /> : null}
        {checklist.error ? <ErrorNote message={checklist.error} /> : null}

        {checklist.data ? (
          <div className="rise flex flex-col gap-5">
            <div className="flex items-center justify-between border-b border-line-dim pb-3">
              <Label faint>
                {checklist.data.count} obligations · {humanise(actor)}
                {tier ? ` · ${tierLabel(tier)}` : ""}
              </Label>
              <button
                onClick={() =>
                  onAsk(
                    `List the compliance obligations for a ${humanise(actor).toLowerCase()}${
                      tier ? ` of a ${tierLabel(tier).toLowerCase()} system` : ""
                    }, and explain what each one practically requires.`
                  )
                }
                className="font-mono text-[10px] uppercase tracking-[0.24em] text-text-dim transition-colors hover:text-text-ghost"
              >
                explain with the agent →
              </button>
            </div>

            <ul className="flex flex-col divide-y divide-line-dim border-y border-line-dim">
              {(checklist.data.items ?? []).map((item, index) => {
                const key = `${index}:${item.ref}`;
                const done = Boolean(checked[key]);
                return (
                  <li key={key} className="flex gap-4 py-4">
                    <button
                      onClick={() => setChecked((prev) => ({ ...prev, [key]: !prev[key] }))}
                      aria-label={done ? "mark incomplete" : "mark complete"}
                      className={`mt-[3px] h-[15px] w-[15px] shrink-0 border transition-colors ${
                        done
                          ? "border-text-ghost bg-text-ghost"
                          : "border-line-hi hover:border-text-ghost"
                      }`}
                    />
                    <div className="flex flex-col gap-2">
                      <div className="flex flex-wrap items-baseline gap-3">
                        <span
                          className={`font-display text-[15px] leading-snug ${
                            done ? "text-text-faint line-through" : "text-text-ghost"
                          }`}
                        >
                          {item.title}
                        </span>
                        <span className="font-mono text-[10px] text-text-faint">{item.ref}</span>
                      </div>
                      <p className="font-display text-[13px] leading-relaxed text-text-dim">
                        {item.description}
                      </p>
                      <p className="font-display text-[13px] leading-relaxed text-text-faint">
                        <span className="font-mono text-[10px] uppercase tracking-[0.18em]">
                          action ·{" "}
                        </span>
                        {item.action}
                      </p>
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        ) : !checklist.loading ? (
          <EmptyNote>Pick an actor and generate a checklist.</EmptyNote>
        ) : null}
      </div>
    </div>
  );
}
