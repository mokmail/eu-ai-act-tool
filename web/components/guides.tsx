"use client";

/**
 * Procedures and Cases — the "apply it" half of the app.
 *
 * Procedures are step-by-step and every step cites its article. Cases are worked
 * examples: a description of a system, the tier it lands in, and why — each item
 * anchored to a provision.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { api, humanise, tierLabel } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { StepFlow } from "@/components/diagrams";
import { Badge, EmptyNote, ErrorNote, Label, Panel, Spinner, ViewHeader } from "@/components/shell";

const refToArticle = (ref: string) => ref.match(/^Article (\S+?)(?:\(|$)/)?.[1];

const TIER_TONE: Record<string, "ghost" | "outline" | "dim"> = {
  prohibited: "ghost",
  high_risk: "ghost",
  gpai_systemic: "ghost",
  gpai: "outline",
  limited_risk: "outline",
  minimal_risk: "dim",
};

/* ===========================================================================
   Procedures
=========================================================================== */
export function ProceduresView({
  onOpenArticle,
  onAsk,
}: {
  onOpenArticle: (n: string) => void;
  onAsk: (text: string) => void;
}) {
  const list = useApi(api.procedures);
  const one = useApi(api.procedure);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    void list.run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [list.run]);

  const open = useCallback(
    async (id: string) => {
      setSelected(id);
      await one.run(id);
    },
    [one]
  );

  useEffect(() => {
    void open("classify");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const stepRef = (ref: string) => {
    const n = refToArticle(ref);
    if (n) onOpenArticle(n);
  };

  return (
    <div className="h-full overflow-y-auto px-5 py-8 md:px-8">
      <div className="mx-auto flex max-w-[1000px] flex-col gap-8">
        <ViewHeader
          eyebrow="procedures"
          title="What to do, in order"
          lede="The Act is written as obligations, not as workflows. These are the workflows: every step names the article it comes from."
        />

        <div className="flex flex-col gap-3">
          <Label faint>{list.data?.items.length ?? 0} procedures</Label>
          <div className="flex flex-col divide-y divide-line-dim border-y border-line-dim">
            {(list.data?.items ?? []).map((p) => {
              const on = selected === p.id;
              return (
                <button
                  key={p.id}
                  onClick={() => open(p.id)}
                  className={`group flex flex-col gap-1 border-l py-3 pl-4 pr-2 text-left transition-colors ${
                    on ? "border-text-ghost" : "border-transparent hover:border-line-hi"
                  }`}
                >
                  <span className="flex flex-wrap items-baseline gap-3">
                    <span className={`font-display text-[15px] ${on ? "text-text-ghost" : "text-text-dim group-hover:text-text-ghost"}`}>
                      {p.title}
                    </span>
                    <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-text-faint">
                      {humanise(p.actor)}
                    </span>
                    <span className="ml-auto font-mono text-[10px] text-text-faint">
                      {p.steps} steps · {p.ref}
                    </span>
                  </span>
                  <span className="font-display text-[12px] leading-relaxed text-text-faint">{p.summary}</span>
                </button>
              );
            })}
          </div>
          {list.loading ? <Spinner label="loading" /> : null}
          {list.error ? <ErrorNote message={list.error} /> : null}
        </div>

        {one.loading ? <Spinner label="loading procedure" /> : null}
        {one.error ? <ErrorNote message={one.error} /> : null}

        {one.data ? (
          <Panel className="rise flex flex-col gap-6 px-5 py-6 md:px-7">
            <header className="flex flex-col gap-3 border-b border-line-dim pb-5">
              <div className="flex flex-wrap items-center gap-2">
                {one.data.actor ? (
                  <Badge tone="outline">{humanise(one.data.actor)}</Badge>
                ) : null}
                {one.data.tier ? (
                  <Badge tone="outline">{humanise(one.data.tier)}</Badge>
                ) : null}
                <span className="font-mono text-[10px] text-text-faint">{one.data.ref}</span>
              </div>
              <h2 className="font-display text-[clamp(1.25rem,2vw,1.7rem)] font-light leading-tight tracking-[-0.02em] text-text-ghost">
                {one.data.title}
              </h2>
              <p className="max-w-[74ch] font-display text-[14px] leading-relaxed text-text-dim">
                {one.data.summary}
              </p>
            </header>

            <StepFlow steps={one.data.steps} onOpen={stepRef} />

            <button
              onClick={() =>
                onAsk(
                  `Walk me through "${one.data?.title}" and tell me what evidence I need to keep at each step, citing the articles.`
                )
              }
              className="self-start border border-line-hi px-4 py-2 font-mono text-[10px] uppercase tracking-[0.24em] text-text-ghost transition-opacity hover:opacity-60"
            >
              ask the agent to expand this →
            </button>
          </Panel>
        ) : null}
      </div>
    </div>
  );
}

/** Case cards per page. Enough to scan one screen, few enough that pagination stays honest. */
const PAGE_SIZE = 12;

/* ===========================================================================
   Cases
=========================================================================== */
export function CasesView({
  onOpenArticle,
  onAsk,
}: {
  onOpenArticle: (n: string) => void;
  onAsk: (text: string) => void;
}) {
  const list = useApi(api.scenarios);
  const one = useApi(api.scenario);
  const [selected, setSelected] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [tier, setTier] = useState<string | null>(null);
  const [sector, setSector] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const detail = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    void list.run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [list.run]);

  const open = useCallback(
    async (id: string) => {
      setSelected(id);
      await one.run(id);
      // the case renders below a long list, so bring it into view
      detail.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    },
    [one]
  );

  const items = useMemo(() => list.data?.items ?? [], [list.data]);

  const tiers = useMemo(() => [...new Set(items.map((s) => s.tier))].sort(), [items]);
  const sectors = useMemo(() => [...new Set(items.map((s) => s.sector))].sort(), [items]);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return items.filter((s) => {
      if (tier && s.tier !== tier) return false;
      if (sector && s.sector !== sector) return false;
      if (!needle) return true;
      return `${s.title} ${s.summary ?? ""} ${s.sector} ${s.tier} ${(s.refs ?? []).join(" ")}`
        .toLowerCase()
        .includes(needle);
    });
  }, [items, query, tier, sector]);

  // any change to the filter restarts the run through the results
  useEffect(() => {
    setPage(1);
  }, [query, tier, sector]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const here = Math.min(page, pageCount);
  const pageItems = filtered.slice((here - 1) * PAGE_SIZE, here * PAGE_SIZE);
  const filtering = Boolean(query.trim() || tier || sector);

  const stepRef = (ref: string) => {
    const n = refToArticle(ref);
    if (n) onOpenArticle(n);
  };

  return (
    <div className="h-full overflow-y-auto px-5 py-8 md:px-8">
      <div className="mx-auto flex max-w-[1000px] flex-col gap-8">
        <ViewHeader
          eyebrow="cases"
          title="The Act applied"
          lede="Worked examples: a system, the tier it lands in, and the reasoning — every claim anchored to a provision. Illustrative, not enforcement decisions."
        />

        {/* with dozens of cases, finding one matters more than listing them all */}
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center gap-x-5 gap-y-3">
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="search cases…"
              aria-label="Search cases"
              spellCheck={false}
              className="w-full max-w-[300px] border border-line-dim bg-bg-panel px-3 py-2 font-mono text-[11px] text-text-ghost outline-none transition-colors placeholder:text-text-faint focus:border-line-hi"
            />
            <select
              value={sector ?? ""}
              onChange={(event) => setSector(event.target.value || null)}
              aria-label="Filter by sector"
              className="border border-line-dim bg-bg-panel px-3 py-2 font-mono text-[11px] uppercase tracking-[0.1em] text-text-ghost outline-none transition-colors focus:border-line-hi"
            >
              <option value="">every sector</option>
              {sectors.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            <Label faint>
              {filtered.length} of {items.length}
            </Label>
            {filtering ? (
              <button
                type="button"
                onClick={() => {
                  setQuery("");
                  setTier(null);
                  setSector(null);
                }}
                className="font-mono text-[10px] uppercase tracking-[0.2em] text-text-dim transition-colors hover:text-text-ghost"
              >
                clear
              </button>
            ) : null}
          </div>

          {tiers.length > 1 ? (
            <div className="flex flex-wrap items-center gap-2">
              <Label faint>tier</Label>
              {tiers.map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setTier(tier === t ? null : t)}
                  aria-pressed={tier === t}
                  className={`border px-2 py-1 font-mono text-[10px] uppercase tracking-[0.16em] transition-colors ${
                    tier === t
                      ? "border-text-ghost text-text-ghost"
                      : "border-line-dim text-text-dim hover:border-line-hi hover:text-text-ghost"
                  }`}
                >
                  {tierLabel(t)}
                </button>
              ))}
            </div>
          ) : null}
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {pageItems.map((s) => {
            const on = selected === s.id;
            return (
              <button
                key={s.id}
                onClick={() => open(s.id)}
                className={`flex flex-col gap-2 border px-4 py-4 text-left transition-colors ${
                  on ? "border-text-ghost bg-bg-panel" : "border-line-dim hover:border-line-hi"
                }`}
              >
                <span className="flex items-center gap-2">
                  <Badge tone={TIER_TONE[s.tier] ?? "outline"}>{tierLabel(s.tier)}</Badge>
                  <span className="ml-auto font-mono text-[10px] uppercase tracking-[0.16em] text-text-faint">
                    {s.sector}
                  </span>
                </span>
                <span className={`font-display text-[14px] leading-snug ${on ? "text-text-ghost" : "text-text-dim"}`}>
                  {s.title}
                </span>
              </button>
            );
          })}
        </div>

        {!list.loading && !list.error && items.length > 0 && !filtered.length ? (
          <EmptyNote>
            No case matches that. Clear the filters to see all {items.length}.
          </EmptyNote>
        ) : null}

        {pageCount > 1 ? (
          <div className="flex flex-wrap items-center justify-between gap-4 border-t border-line-dim pt-4">
            <Label faint>
              page {here} of {pageCount}
            </Label>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setPage(here - 1)}
                disabled={here <= 1}
                className="border border-line-dim px-3 py-1 font-mono text-[10px] uppercase tracking-[0.18em] text-text-dim transition-colors hover:border-line-hi hover:text-text-ghost disabled:opacity-30"
              >
                ← prev
              </button>
              <button
                type="button"
                onClick={() => setPage(here + 1)}
                disabled={here >= pageCount}
                className="border border-line-dim px-3 py-1 font-mono text-[10px] uppercase tracking-[0.18em] text-text-dim transition-colors hover:border-line-hi hover:text-text-ghost disabled:opacity-30"
              >
                next →
              </button>
            </div>
          </div>
        ) : null}

        {list.loading ? <Spinner label="loading cases" /> : null}
        {list.error ? <ErrorNote message={list.error} /> : null}

        <div ref={detail} className="scroll-mt-24" aria-hidden />

        {one.loading ? <Spinner label="loading case" /> : null}
        {one.error ? <ErrorNote message={one.error} /> : null}

        {one.data ? (
          <Panel className="rise flex flex-col gap-6 px-5 py-6 md:px-7">
            <header className="flex flex-col gap-3 border-b border-line-dim pb-5">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={TIER_TONE[one.data.tier] ?? "outline"}>{tierLabel(one.data.tier)}</Badge>
                <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-text-faint">
                  {one.data.sector}
                </span>
              </div>
              <h2 className="font-display text-[clamp(1.25rem,2vw,1.7rem)] font-light leading-tight tracking-[-0.02em] text-text-ghost">
                {one.data.title}
              </h2>
              <p className="max-w-[74ch] font-display text-[14px] leading-relaxed text-text-dim">
                {one.data.summary}
              </p>
              <ul className="flex flex-wrap gap-2 pt-1">
                {one.data.refs.map((r) => (
                  <li key={r}>
                    <button onClick={() => stepRef(r)} className="transition-opacity hover:opacity-60">
                      <Badge tone="outline">{r}</Badge>
                    </button>
                  </li>
                ))}
              </ul>
            </header>

            {one.data.roles.length ? (
              <div className="grid gap-4 sm:grid-cols-3">
                {one.data.roles.map((r) => (
                  <div key={r.role} className="flex flex-col gap-1 border-l border-line-dim pl-3">
                    <Label faint>{r.role}</Label>
                    <span className="font-display text-[12px] leading-relaxed text-text-dim">{r.who}</span>
                  </div>
                ))}
              </div>
            ) : null}

            <ol className="flex flex-col divide-y divide-line-dim border-y border-line-dim">
              {one.data.analysis.map((item, i) => (
                <li key={i} className="flex flex-col gap-2 py-4">
                  <div className="flex flex-wrap items-baseline gap-3">
                    <span className="font-display text-[15px] text-text-ghost">{item.title}</span>
                    <button
                      onClick={() => stepRef(item.ref)}
                      className="font-mono text-[10px] uppercase tracking-[0.16em] text-text-faint transition-colors hover:text-text-ghost"
                    >
                      {item.ref}
                    </button>
                  </div>
                  <p className="max-w-[74ch] font-display text-[13px] leading-relaxed text-text-dim">
                    {item.detail}
                  </p>
                </li>
              ))}
            </ol>

            {one.data.watchouts.length ? (
              <div className="flex flex-col gap-2">
                <Label faint>watch out</Label>
                <ul className="flex flex-col gap-2">
                  {one.data.watchouts.map((w) => (
                    <li key={w} className="flex gap-3 font-display text-[13px] leading-relaxed text-text-dim">
                      <span className="text-text-faint">!</span>
                      <span>{w}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            <p className="font-display text-[11px] leading-relaxed text-text-faint">
              {one.data.disclaimer ??
                "Illustrative example built from the Act's own text — not an enforcement decision."}
            </p>

            <button
              onClick={() =>
                onAsk(
                  `Take the scenario "${one.data?.title}" and tell me exactly what the provider and the deployer must each do, with the articles and the deadlines.`
                )
              }
              className="self-start border border-line-hi px-4 py-2 font-mono text-[10px] uppercase tracking-[0.24em] text-text-ghost transition-opacity hover:opacity-60"
            >
              ask the agent about this case →
            </button>
          </Panel>
        ) : !one.loading && !one.error && !selected ? (
          <EmptyNote>Pick a case above.</EmptyNote>
        ) : null}
      </div>
    </div>
  );
}
