"use client";

/**
 * Overview — the dashboard, and the only place the corpus is measured.
 *
 * This page absorbed the separate Charts view: the citation graph, the
 * organigram, the chapter weights and the timeline were all one question asked
 * in six parts, and splitting them across two destinations meant the same
 * numbers were drawn twice.
 *
 * The page is six tabs, each answering one question, with the masthead and the
 * tab bar staying put. Every figure is computed from the shipped EUR-Lex text
 * and the curated layer, so the landing page can never drift from what the app
 * actually contains.
 */

import { useEffect, useMemo, useRef, useState } from "react";

import { api, humanise, type GovernanceNode } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import {
  BarChart,
  CitationGraph,
  OrgChart,
  TimelineChart,
  type OrgNode,
} from "@/components/diagrams";
import { ErrorNote, Label, Panel, Spinner, ViewHeader } from "@/components/shell";
import { useCountUp, useInView } from "@/components/viz";
import type { ViewKey } from "@/components/shell";

/* ---------------------------------------------------------------------------
   A headline figure that counts up as the tab appears.
--------------------------------------------------------------------------- */
function Figure({
  count,
  suffix = "",
  value,
  label,
  note,
}: {
  count?: number;
  suffix?: string;
  value?: string;
  label: string;
  note?: string;
}) {
  const { ref, seen } = useInView<HTMLDivElement>();
  const animated = useCountUp(count ?? 0, count !== undefined && seen);
  const shown = count !== undefined ? `${animated.toLocaleString()}${suffix}` : value ?? "—";

  return (
    <div ref={ref} className="flex flex-col gap-2 border-t border-line-dim pt-4">
      <span className="font-display text-[clamp(1.6rem,2.6vw,2.3rem)] font-light leading-none tracking-[-0.03em] text-text-ghost">
        {shown}
      </span>
      <Label>{label}</Label>
      {note ? (
        <span className="font-display text-[11px] leading-snug text-text-faint">{note}</span>
      ) : null}
    </div>
  );
}

function SectionHead({
  label,
  body,
  aside,
}: {
  label: string;
  body?: string;
  aside?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-2 pb-6">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <Label>{label}</Label>
        {aside}
      </div>
      {body ? (
        <p className="max-w-[70ch] font-display text-[13px] leading-relaxed text-text-dim">{body}</p>
      ) : null}
    </div>
  );
}

/**
 * Where a tier sits on the brand's own axis: banned → safe. The card wears the
 * colour, not just a dot: a band across the top, a wash behind the content, and
 * the tier's own name in its own ink.
 */
const TIER_CARD: Record<string, { band: string; wash: string; dot: string; ink: string }> = {
  prohibited: {
    band: "bg-alert",
    wash: "bg-alert/5",
    dot: "bg-alert",
    ink: "text-alert",
  },
  high_risk: {
    band: "bg-text-ghost",
    wash: "bg-text-ghost/5",
    dot: "bg-text-ghost",
    ink: "text-text-ghost",
  },
  limited_risk: {
    band: "bg-text-dim",
    wash: "bg-text-dim/5",
    dot: "bg-text-dim",
    ink: "text-text-dim",
  },
  minimal_risk: {
    band: "bg-accent",
    wash: "bg-accent/10",
    dot: "bg-accent",
    ink: "text-accent",
  },
};

const PATHS: { key: ViewKey; step: string; title: string; body: string }[] = [
  {
    key: "classify",
    step: "01",
    title: "Classify the system",
    body: "Answer the Act’s own questions and land on a tier — with the obligations that follow.",
  },
  {
    key: "map",
    step: "02",
    title: "Read the provision",
    body: "Navigate all 113 articles, 180 recitals and 13 annexes, and see what each one cites.",
  },
  {
    key: "procedures",
    step: "03",
    title: "Follow the procedure",
    body: "Conformity assessment, deployer duties, FRIA, incident reporting — step by step.",
  },
  {
    key: "cases",
    step: "04",
    title: "Check the cases",
    body: "Seven worked examples, from CV screening to frontier models, with the reasoning shown.",
  },
];

const TABS = [
  { key: "overview", label: "Overview", hint: "The headline numbers" },
  { key: "structure", label: "Structure", hint: "How the text is weighted" },
  { key: "obligations", label: "Obligations", hint: "Who carries the load" },
  { key: "citations", label: "Citations", hint: "Where the text points" },
  { key: "governance", label: "Governance", hint: "Who administers the Act" },
  { key: "timeline", label: "Timeline", hint: "When it applies" },
] as const;

type TabKey = (typeof TABS)[number]["key"];

/** The governance tree arrives nested to arbitrary depth; carry all of it. */
function toOrgNode(node: GovernanceNode): OrgNode {
  return {
    name: node.name,
    ref: node.ref,
    note: node.note,
    advisory: node.advisory,
    children: node.children?.map(toOrgNode),
  };
}

export function DashboardView({
  onSelect,
  onOpenArticle,
  onAsk,
}: {
  onSelect: (v: ViewKey) => void;
  onOpenArticle: (n: string) => void;
  onAsk: (text: string) => void;
}) {
  const stats = useApi(api.stats);
  const graph = useApi(api.graph);
  const timeline = useApi(api.timeline);
  const tiers = useApi(api.tiers);
  const governance = useApi(api.governanceStructure);

  const [tab, setTab] = useState<TabKey>("overview");
  const scroller = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    void stats.run();
    void graph.run();
    void timeline.run();
    void tiers.run();
    void governance.run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // a tab change should start at the top of the panel, not wherever the last one was
  useEffect(() => {
    scroller.current?.scrollTo({ top: 0, behavior: "smooth" });
  }, [tab]);

  const openRef = (ref: string) => {
    const match = ref.match(/^Article (\S+?)(?:\(|$)/);
    if (match) onOpenArticle(match[1]);
  };

  const corpus = stats.data?.corpus;

  const chaptersByArticles = useMemo(
    () =>
      stats.data?.chapters.map((c) => ({
        label: `${c.number} · ${c.title.length > 22 ? `${c.title.slice(0, 21)}…` : c.title}`,
        value: c.articles,
      })) ?? [],
    [stats.data]
  );

  const chaptersByWords = useMemo(
    () =>
      stats.data?.chapters
        .slice()
        .sort((a, b) => b.words - a.words)
        .slice(0, 8)
        .map((c) => ({
          label: `${c.number} · ${c.title.length > 22 ? `${c.title.slice(0, 21)}…` : c.title}`,
          value: c.words,
        })) ?? [],
    [stats.data]
  );

  const chapterThreeShare = useMemo(() => {
    if (!stats.data) return 0;
    const chapterThree = stats.data.chapters.find((c) => c.number === "III")?.words ?? 0;
    return Math.round((chapterThree / stats.data.corpus.words) * 100);
  }, [stats.data]);

  return (
    <div ref={scroller} className="h-full overflow-y-auto">
      <div className="mx-auto max-w-[1500px] px-5 py-10 md:px-10">
        {/* -- masthead: stays on every tab -- */}
        <div className="flex flex-col gap-8 pb-10">
          <ViewHeader
            eyebrow="overview"
            title="Read the Act. Then apply it."
            lede="Regulation (EU) 2024/1689 is long, and written as obligations rather than instructions. This app puts the whole text under your hand — searchable, structured, and paired with the procedures and worked cases that turn it into something you can act on."
          />
          <div className="flex flex-wrap items-center gap-4">
            <button onClick={() => onSelect("ask")} className="menu-cta">
              ask the act →
            </button>
            <button
              onClick={() => onSelect("classify")}
              className="border border-line-hi px-4 py-2 font-mono text-[10px] uppercase tracking-[0.28em] text-text-ghost transition-opacity hover:opacity-60"
            >
              walk the classification ladder
            </button>
          </div>
        </div>

        {/* -- tabs: sticky, so the section is always named on screen -- */}
        <div
          role="tablist"
          aria-label="Dashboard sections"
          className="sticky top-0 z-20 -mx-5 flex gap-1 overflow-x-auto border-b border-line-dim bg-bg-void/90 px-5 backdrop-blur-md md:-mx-10 md:px-10"
        >
          {TABS.map((item) => {
            const active = item.key === tab;
            return (
              <button
                key={item.key}
                role="tab"
                aria-selected={active}
                onClick={() => setTab(item.key)}
                className={`shrink-0 border-b-2 px-3 py-3 text-left transition-colors first:pl-0 md:px-4 ${
                  active ? "border-text-ghost" : "border-transparent hover:border-line-hi"
                }`}
              >
                <span
                  className={`block font-mono text-[10px] uppercase tracking-[0.24em] transition-colors ${
                    active ? "text-text-ghost" : "text-text-dim"
                  }`}
                >
                  {item.label}
                </span>
                <span className="mt-1 hidden font-display text-[11px] leading-tight text-text-faint sm:block">
                  {item.hint}
                </span>
              </button>
            );
          })}
        </div>

        {/* ================= OVERVIEW ================= */}
        {tab === "overview" ? (
          <div className="flex flex-col gap-12 pt-10">
            {stats.loading && !corpus ? <Spinner label="reading the Act" /> : null}
            {stats.error ? <ErrorNote message={stats.error} /> : null}

            {corpus ? (
              <section className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
                <Figure count={corpus.articles} label="articles" note="binding text, by chapter" />
                <Figure count={corpus.recitals} label="recitals" note="the intent behind them" />
                <Figure count={corpus.annexes} label="annexes" note="technical detail" />
                <Figure
                  value={`${corpus.chapters}·${corpus.sections}`}
                  label="chapters · sections"
                  note="the Act’s own skeleton"
                />
                <Figure
                  count={Math.round(corpus.words / 1000)}
                  suffix="k"
                  label="words"
                  note={`+${Math.round(corpus.recital_words / 1000)}k in recitals`}
                />
                <Figure
                  count={graph.data?.edge_count}
                  value={graph.data ? undefined : "—"}
                  label="cross-references"
                  note="article-to-article citations"
                />
              </section>
            ) : null}

            {tiers.data ? (
              <section>
                <SectionHead
                  label="the four tiers"
                  body="The Act does not regulate “AI”. It regulates AI by risk, and the tier decides everything else."
                />
                <div className="grid gap-px bg-line-dim sm:grid-cols-2 lg:grid-cols-4">
                  {tiers.data.items.map((tier) => {
                    const style = TIER_CARD[tier.tier] ?? {
                      band: "bg-text-faint",
                      wash: "bg-text-faint/5",
                      dot: "bg-text-faint",
                      ink: "text-text-ghost",
                    };
                    return (
                      <button
                        key={tier.tier}
                        onClick={() => onSelect("classify")}
                        className="group relative flex flex-col overflow-hidden bg-bg-void px-5 py-6 text-left transition-colors hover:bg-bg-panel"
                      >
                        {/* the tier's colour, worn by the card itself */}
                        <span className={`absolute inset-0 ${style.wash}`} aria-hidden />
                        <span
                          className={`absolute inset-x-0 top-0 h-[4px] ${style.band}`}
                          aria-hidden
                        />

                        <div className="relative flex flex-col gap-3">
                          {/* the dot rides the first line even when the label wraps */}
                          <span className="flex items-start gap-3">
                            <span
                              className={`mt-[7px] inline-block h-[8px] w-[8px] shrink-0 ${style.dot}`}
                              aria-hidden
                            />
                            <span
                              className={`font-mono text-[14px] uppercase leading-[1.45] tracking-[0.14em] ${style.ink}`}
                            >
                              {tier.label}
                            </span>
                          </span>
                          <span className="font-display text-[12px] leading-relaxed text-text-dim">
                            {tier.summary.length > 150
                              ? `${tier.summary.slice(0, 149)}…`
                              : tier.summary}
                          </span>
                          <span className="mt-auto flex flex-col gap-1 pt-2">
                            <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-text-faint">
                              from {tier.applies_from}
                            </span>
                            <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-text-faint">
                              {tier.legal_basis}
                            </span>
                          </span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </section>
            ) : null}

            <section>
              <SectionHead label="start here" body="Four moves, in the order most people need them." />
              <div className="grid gap-px bg-line-dim sm:grid-cols-2 lg:grid-cols-4">
                {PATHS.map((path) => (
                  <button
                    key={path.key}
                    onClick={() => onSelect(path.key)}
                    className="group flex flex-col gap-3 bg-bg-void px-5 py-6 text-left transition-colors hover:bg-bg-panel"
                  >
                    <span className="font-mono text-[10px] tabular-nums text-text-faint">
                      {path.step}
                    </span>
                    <span className="font-display text-[15px] leading-snug text-text-ghost">
                      {path.title}
                    </span>
                    <span className="font-display text-[12px] leading-relaxed text-text-dim">
                      {path.body}
                    </span>
                    <span className="mt-auto pt-2 font-mono text-[10px] uppercase tracking-[0.24em] text-text-faint transition-colors group-hover:text-text-ghost">
                      open →
                    </span>
                  </button>
                ))}
              </div>
            </section>

            <section className="flex flex-col gap-3 pb-4">
              <Label faint>provenance</Label>
              <p className="max-w-[86ch] font-display text-[12px] leading-relaxed text-text-faint">
                The full text is extracted from the official EUR-Lex publication of Regulation (EU)
                2024/1689 — 180 recitals, 113 articles and 13 annexes — and the chapter and section
                structure is parsed from that same document. Statistics, the citation graph and every
                mindmap are computed from it. The procedures and cases are curated, and each step
                cites the provision it comes from. This is a compliance aid, not legal advice.
              </p>
              <button
                onClick={() =>
                  onAsk(
                    "Give me a five-minute orientation to the EU AI Act: what it regulates, what the four risk tiers are, and what a company should do first."
                  )
                }
                className="self-start font-mono text-[10px] uppercase tracking-[0.24em] text-text-dim transition-colors hover:text-text-ghost"
              >
                ask for a five-minute orientation →
              </button>
            </section>
          </div>
        ) : null}

        {/* ================= STRUCTURE ================= */}
        {tab === "structure" ? (
          <div className="flex flex-col gap-12 pt-10">
            {stats.error ? <ErrorNote message={stats.error} /> : null}

            {stats.data ? (
              <section className="grid gap-12 lg:grid-cols-2">
                <div className="flex flex-col gap-5">
                  <div className="flex flex-col gap-2">
                    <Label>the Act is not evenly weighted</Label>
                    <p className="max-w-[46ch] font-display text-[13px] leading-relaxed text-text-dim">
                      Chapter III alone carries {chapterThreeShare}% of the operative text. Where the
                      words pile up is where the obligations are.
                    </p>
                  </div>
                  <BarChart data={chaptersByArticles} />
                  <Label faint>articles per chapter · hover a row for the count</Label>
                </div>

                <div className="flex flex-col gap-5">
                  <div className="flex flex-col gap-2">
                    <Label>where the words are</Label>
                    <p className="max-w-[46ch] font-display text-[13px] leading-relaxed text-text-dim">
                      The eight heaviest chapters by word count. Article 113 tells you when each
                      part applies; Article 3 defines the whole vocabulary. Both are worth reading
                      first.
                    </p>
                  </div>
                  <BarChart data={chaptersByWords} />
                  <div className="flex flex-wrap gap-5">
                    <button
                      onClick={() => onOpenArticle("113")}
                      className="font-mono text-[10px] uppercase tracking-[0.24em] text-text-dim transition-colors hover:text-text-ghost"
                    >
                      read article 113 →
                    </button>
                    <button
                      onClick={() => onOpenArticle("3")}
                      className="font-mono text-[10px] uppercase tracking-[0.24em] text-text-dim transition-colors hover:text-text-ghost"
                    >
                      read article 3 →
                    </button>
                  </div>
                </div>
              </section>
            ) : (
              <Spinner label="measuring the text" />
            )}

            {stats.data ? (
              <section>
                <SectionHead
                  label="long and short"
                  body="Where the Act is dense and where it is terse — a proxy for how much reading a provision asks of you."
                />
                <div className="grid gap-12 lg:grid-cols-2">
                  <BarChart
                    data={stats.data.longest_articles.slice(0, 8).map((a) => ({
                      label: a.ref,
                      value: a.words,
                      ref: a.ref,
                    }))}
                    onSelect={openRef}
                  />
                  <BarChart
                    data={stats.data.shortest_articles.slice(0, 8).map((a) => ({
                      label: a.ref,
                      value: a.words,
                      ref: a.ref,
                    }))}
                    onSelect={openRef}
                  />
                </div>
              </section>
            ) : null}
          </div>
        ) : null}

        {/* ================= OBLIGATIONS ================= */}
        {tab === "obligations" ? (
          <div className="flex flex-col gap-12 pt-10">
            {stats.error ? <ErrorNote message={stats.error} /> : null}

            {stats.data ? (
              <section className="grid gap-12 lg:grid-cols-2">
                <div className="flex flex-col gap-5">
                  <div className="flex flex-col gap-2">
                    <Label>who carries the load</Label>
                    <p className="max-w-[46ch] font-display text-[13px] leading-relaxed text-text-dim">
                      Of the {stats.data.obligations.total} obligations indexed here, the bulk land
                      on providers. The deployer’s duties are fewer but harder to delegate.
                    </p>
                  </div>
                  <BarChart
                    data={Object.entries(stats.data.obligations.by_actor).map(([key, value]) => ({
                      label: humanise(key),
                      value,
                    }))}
                  />
                  <button
                    onClick={() => onSelect("comply")}
                    className="self-start font-mono text-[10px] uppercase tracking-[0.24em] text-text-dim transition-colors hover:text-text-ghost"
                  >
                    open the checklists →
                  </button>
                </div>

                <div className="flex flex-col gap-5">
                  <div className="flex flex-col gap-2">
                    <Label>by risk tier</Label>
                    <p className="max-w-[46ch] font-display text-[13px] leading-relaxed text-text-dim">
                      The heavier the tier, the more there is to do — and the higher the ceiling on
                      the fine.
                    </p>
                  </div>
                  <BarChart
                    data={Object.entries(stats.data.obligations.by_tier).map(([key, value]) => ({
                      label: humanise(key),
                      value,
                    }))}
                  />
                  <button
                    onClick={() => onSelect("classify")}
                    className="self-start font-mono text-[10px] uppercase tracking-[0.24em] text-text-dim transition-colors hover:text-text-ghost"
                  >
                    walk the classification ladder →
                  </button>
                </div>
              </section>
            ) : (
              <Spinner label="counting the obligations" />
            )}
          </div>
        ) : null}

        {/* ================= CITATIONS ================= */}
        {tab === "citations" ? (
          <div className="flex flex-col gap-12 pt-10">
            {graph.error ? <ErrorNote message={graph.error} /> : null}

            {graph.data ? (
              <>
                <section className="flex flex-col gap-5">
                  <SectionHead
                    label="the citation graph"
                    body="Which provision points at which, mined from the article text. Drag to pan, scroll to zoom, and click a node to isolate its neighbourhood."
                    aside={
                      <Label faint>
                        {graph.data.edge_count} cross-references · {graph.data.nodes.length} provisions
                      </Label>
                    }
                  />
                  {/* capped: the canvas is square, so its height tracks its width */}
                  <div className="max-w-[860px]">
                    <CitationGraph
                      nodes={graph.data.nodes}
                      edges={graph.data.edges}
                      onSelect={openRef}
                    />
                  </div>
                </section>

                <section className="flex flex-col gap-5 border-t border-line-dim pt-8">
                  <SectionHead
                    label="where the text points"
                    body="The most-cited provisions in the Act. Annex III is referenced more than any other part — it is where high-risk actually gets defined."
                  />
                  <div className="max-w-[860px]">
                    <BarChart
                      data={graph.data.most_cited.slice(0, 12).map((item) => ({
                        label: item.ref,
                        value: item.citations,
                        ref: item.ref,
                      }))}
                      onSelect={openRef}
                    />
                    <p className="mt-4 font-mono text-[10px] uppercase tracking-[0.2em] text-text-faint">
                      click a row to open the provision
                    </p>
                  </div>
                </section>
              </>
            ) : (
              <Spinner label="tracing the references" />
            )}
          </div>
        ) : null}

        {/* ================= GOVERNANCE ================= */}
        {tab === "governance" ? (
          <div className="flex flex-col gap-12 pt-10">
            {governance.error ? <ErrorNote message={governance.error} /> : null}

            {governance.data ? (
              <>
                <section className="flex flex-col gap-5">
                  <SectionHead
                    label="who administers the Act"
                    body={governance.data.note}
                    aside={
                      <button
                        onClick={() => onOpenArticle("64")}
                        className="font-mono text-[10px] uppercase tracking-[0.24em] text-text-dim transition-colors hover:text-text-ghost"
                      >
                        article 64 →
                      </button>
                    }
                  />
                  <Panel className="overflow-x-auto px-4 py-6 md:px-6">
                    <div className="min-w-[720px]">
                      <OrgChart root={toOrgNode(governance.data.root)} onSelect={openRef} />
                    </div>
                  </Panel>
                </section>

                <section className="grid gap-7 border-t border-line-dim pt-8 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                  {[
                    ...(governance.data.root.children ?? []),
                  ].map((body) => (
                    <div key={body.ref} className="flex flex-col gap-2 border-t border-line-dim pt-4">
                      <span className="font-display text-[14px] leading-snug text-text-ghost">
                        {body.name}
                      </span>
                      <button
                        onClick={() => openRef(body.ref)}
                        className="w-fit font-mono text-[10px] uppercase tracking-[0.16em] text-text-faint transition-colors hover:text-text-ghost"
                      >
                        {body.ref}
                      </button>
                      {body.note ? (
                        <span className="font-display text-[11px] leading-relaxed text-text-faint">
                          {body.note}
                        </span>
                      ) : null}
                    </div>
                  ))}
                </section>
              </>
            ) : (
              <Spinner label="drawing the organigram" />
            )}
          </div>
        ) : null}

        {/* ================= TIMELINE ================= */}
        {tab === "timeline" ? (
          <div className="flex flex-col gap-12 pt-10">
            <section className="flex flex-col gap-5">
              <SectionHead
                label="when it applies"
                body="The Act arrived in stages, and the axis below is drawn to scale — which is why the two 2024 dates sit almost on top of each other while 2027 stands alone. The green marker is the next milestone still to come."
                aside={
                  <button
                    onClick={() => onOpenArticle("113")}
                    className="font-mono text-[10px] uppercase tracking-[0.24em] text-text-dim transition-colors hover:text-text-ghost"
                  >
                    article 113 →
                  </button>
                }
              />
              {timeline.data ? (
                <div className="max-w-[900px]">
                  <TimelineChart events={timeline.data.items} onSelect={openRef} />
                </div>
              ) : (
                <Spinner label="loading the timeline" />
              )}
            </section>

            {timeline.data ? (
              <section className="grid gap-8 border-t border-line-dim pt-8 sm:grid-cols-3">
                <Figure count={timeline.data.items.length} label="milestones" note="in Article 113" />
                <Figure
                  count={
                    timeline.data.items.filter((e) => new Date(e.date).getTime() <= Date.now())
                      .length
                  }
                  label="already in force"
                  note="as of today"
                />
                <Figure
                  count={
                    timeline.data.items.filter((e) => new Date(e.date).getTime() > Date.now())
                      .length
                  }
                  label="still to come"
                  note="not yet applicable"
                />
              </section>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}
