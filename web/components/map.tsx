"use client";

/**
 * Map — navigate the Act by its own structure.
 *
 * Three parts — articles (by chapter and section), recitals and annexes — with
 * the open provision on the right, its position in the Act, and its citation
 * neighbourhood. Search runs over the whole corpus.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import {
  api,
  type GraphArticle,
  type ProvisionResult,
  type Structure,
} from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Badge, EmptyNote, ErrorNote, Label, Spinner, ViewHeader } from "@/components/shell";

type Part = "articles" | "recitals" | "annexes";
type Selection = { part: Part; id: string } | null;

const PARTS: { key: Part; label: string }[] = [
  { key: "articles", label: "articles" },
  { key: "recitals", label: "recitals" },
  { key: "annexes", label: "annexes" },
];

function ArticleRow({
  article,
  active,
  onOpen,
}: {
  article: { number: string; title: string };
  active: boolean;
  onOpen: (n: string) => void;
}) {
  return (
    <li>
      <button
        onClick={() => onOpen(article.number)}
        className={`flex w-full items-baseline gap-3 border-l py-1.5 pl-8 pr-5 text-left transition-colors ${
          active ? "border-text-ghost text-text-ghost" : "border-transparent text-text-dim hover:text-text-ghost"
        }`}
      >
        <span className="w-6 shrink-0 font-mono text-[10px] tabular-nums text-text-faint">
          {article.number}
        </span>
        <span className="truncate font-display text-[12px]">{article.title}</span>
      </button>
    </li>
  );
}

export function MapView({ initialArticle }: { initialArticle?: string | null }) {
  const structure = useApi(api.structure);
  const recitalIndex = useApi(api.recitals);
  const annexIndex = useApi(api.annexes);
  const provision = useApi(api.article);
  const location = useApi(api.location);
  const graph = useApi(api.graphArticle);
  const recital = useApi(api.recital);
  const annex = useApi(api.annex);
  const search = useApi(api.search);

  const [part, setPart] = useState<Part>("articles");
  const [open, setOpen] = useState<Record<string, boolean>>({});
  const [selection, setSelection] = useState<Selection>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    void structure.run();
    void recitalIndex.run();
    void annexIndex.run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [structure.run, recitalIndex.run, annexIndex.run]);

  const openArticle = useCallback(
    (n: string) => {
      setPart("articles");
      setSelection({ part: "articles", id: n });
      void provision.run(n);
      void location.run(n);
      void graph.run(n);
    },
    [provision, location, graph]
  );

  const openRecital = useCallback(
    (n: number) => {
      setPart("recitals");
      setSelection({ part: "recitals", id: String(n) });
      void recital.run(n);
    },
    [recital]
  );

  const openAnnex = useCallback(
    (n: string) => {
      setPart("annexes");
      setSelection({ part: "annexes", id: n });
      void annex.run(n);
    },
    [annex]
  );

  useEffect(() => {
    if (initialArticle) openArticle(initialArticle);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialArticle]);

  const toc: Structure | null = structure.data;

  const titleMatches = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q || !toc) return null;
    const hits: { number: string; title: string; chapter: string }[] = [];
    for (const c of toc.chapters) {
      const push = (n: string, t: string) => {
        if (`${n} ${t}`.toLowerCase().includes(q)) hits.push({ number: n, title: t, chapter: c.number });
      };
      c.articles.forEach((a) => push(a.number, a.title));
      c.sections.forEach((s) => s.articles.forEach((a) => push(a.number, a.title)));
    }
    return hits;
  }, [query, toc]);

  const current = selection;
  const showingArticle = current?.part === "articles";
  const body: ProvisionResult | null = showingArticle
    ? provision.data
    : current?.part === "recitals"
      ? recital.data
      : current?.part === "annexes"
        ? annex.data
        : null;
  const busy =
    (showingArticle && provision.loading) ||
    (current?.part === "recitals" && recital.loading) ||
    (current?.part === "annexes" && annex.loading);

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-line-dim px-5 py-6 md:px-8">
        <ViewHeader
          eyebrow="navigate"
          title="The shape of the Act"
          lede="13 chapters, 16 sections, 113 articles, 180 recitals and 13 annexes. The structure is parsed from the official text, so you always know where a provision sits."
        />
        <div className="mt-5 flex flex-wrap items-center gap-x-6 gap-y-2">
          {PARTS.map((p) => (
            <button
              key={p.key}
              onClick={() => setPart(p.key)}
              className={`font-mono text-[10px] uppercase tracking-[0.28em] transition-colors ${
                part === p.key ? "text-text-ghost" : "text-text-dim hover:text-text-ghost"
              }`}
            >
              {p.label}
            </button>
          ))}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (query.trim()) void search.run(query.trim(), "all", 25);
            }}
            className="ml-auto flex min-w-[240px] flex-1 items-center gap-3 border-b border-line-dim pb-1 md:max-w-[46ch]"
          >
            <Label faint>find</Label>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="filter titles, or enter to search the text"
              className="flex-1 bg-transparent font-display text-[13px] text-text-ghost outline-none placeholder:text-text-faint"
            />
          </form>
        </div>
      </div>

      <div className="flex min-h-0 flex-1">
        {/* -- the index -- */}
        <aside className="hidden w-[330px] shrink-0 overflow-y-auto border-r border-line-dim py-5 md:block">
          {part === "articles" ? (
            <>
              {structure.loading && !toc ? (
                <div className="px-5"><Spinner label="parsing the Act" /></div>
              ) : null}
              {structure.error ? <div className="px-5"><ErrorNote message={structure.error} /></div> : null}

              {titleMatches ? (
                <div className="px-5">
                  <Label faint>{titleMatches.length} articles match</Label>
                  <ul className="mt-3 flex flex-col divide-y divide-line-dim">
                    {titleMatches.map((m) => (
                      <li key={m.number}>
                        <button
                          onClick={() => openArticle(m.number)}
                          className={`flex w-full items-baseline gap-3 py-2 text-left transition-colors ${
                            current?.id === m.number && showingArticle
                              ? "text-text-ghost"
                              : "text-text-dim hover:text-text-ghost"
                          }`}
                        >
                          <span className="w-7 shrink-0 font-mono text-[10px] tabular-nums text-text-faint">{m.number}</span>
                          <span className="truncate font-display text-[12px]">{m.title}</span>
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {toc && !titleMatches
                ? toc.chapters.map((chapter) => {
                    const isOpen = open[chapter.number] ?? false;
                    const count = chapter.sections.length
                      ? chapter.sections.reduce((s, x) => s + x.articles.length, 0)
                      : chapter.articles.length;
                    return (
                      <div key={chapter.number} className="mb-1">
                        <button
                          onClick={() => setOpen((prev) => ({ ...prev, [chapter.number]: !isOpen }))}
                          className="flex w-full items-baseline gap-3 px-5 py-2 text-left transition-colors hover:opacity-70"
                        >
                          <span className="font-mono text-[10px] text-text-faint">{isOpen ? "−" : "+"}</span>
                          <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-text-ghost">
                            Ch. {chapter.number}
                          </span>
                          <span className="ml-auto font-mono text-[10px] tabular-nums text-text-faint">{count}</span>
                        </button>
                        {isOpen ? (
                          <p className="px-5 pb-2 font-display text-[11px] leading-snug text-text-faint">
                            {chapter.title}
                          </p>
                        ) : null}

                        {isOpen ? (
                          <ul className="flex flex-col">
                            {/* A chapter either groups its articles under sections, or
                                lists them flat. Rendering both would double every row. */}
                            {chapter.sections.length
                              ? chapter.sections.map((section) => (
                                  <li key={`s-${section.number}`}>
                                    <p className="px-5 pb-1 pt-2 font-mono text-[9px] uppercase tracking-[0.2em] text-text-faint">
                                      §{section.number} {section.title}
                                    </p>
                                    <ul>
                                      {section.articles.map((a) => (
                                        <ArticleRow
                                          key={a.number}
                                          article={a}
                                          active={current?.id === a.number && showingArticle}
                                          onOpen={openArticle}
                                        />
                                      ))}
                                    </ul>
                                  </li>
                                ))
                              : chapter.articles.map((a) => (
                                  <ArticleRow
                                    key={a.number}
                                    article={a}
                                    active={current?.id === a.number && showingArticle}
                                    onOpen={openArticle}
                                  />
                                ))}
                          </ul>
                        ) : null}
                      </div>
                    );
                  })
                : null}
            </>
          ) : null}

          {part === "recitals" ? (
            <ul className="flex flex-col">
              {recitalIndex.loading && !recitalIndex.data ? (
                <li className="px-5"><Spinner label="loading recitals" /></li>
              ) : null}
              {(recitalIndex.data?.items ?? []).map((r) => (
                <li key={r.number}>
                  <button
                    onClick={() => openRecital(r.number)}
                    className={`flex w-full items-baseline gap-3 border-l py-2 pl-5 pr-4 text-left transition-colors ${
                      current?.id === String(r.number) && current.part === "recitals"
                        ? "border-text-ghost text-text-ghost"
                        : "border-transparent text-text-dim hover:text-text-ghost"
                    }`}
                  >
                    <span className="w-7 shrink-0 font-mono text-[10px] tabular-nums text-text-faint">{r.number}</span>
                    <span className="line-clamp-2 font-display text-[11px] leading-snug">{r.title}</span>
                  </button>
                </li>
              ))}
            </ul>
          ) : null}

          {part === "annexes" ? (
            <ul className="flex flex-col">
              {annexIndex.loading && !annexIndex.data ? (
                <li className="px-5"><Spinner label="loading annexes" /></li>
              ) : null}
              {(annexIndex.data?.items ?? []).map((a) => (
                <li key={a.number}>
                  <button
                    onClick={() => openAnnex(a.number)}
                    className={`flex w-full items-baseline gap-3 border-l py-2.5 pl-5 pr-4 text-left transition-colors ${
                      current?.id === a.number && current.part === "annexes"
                        ? "border-text-ghost text-text-ghost"
                        : "border-transparent text-text-dim hover:text-text-ghost"
                    }`}
                  >
                    <span className="w-8 shrink-0 font-mono text-[10px] text-text-faint">{a.number}</span>
                    <span className="line-clamp-2 font-display text-[12px] leading-snug">{a.title}</span>
                  </button>
                </li>
              ))}
            </ul>
          ) : null}
        </aside>

        {/* -- the provision -- */}
        <div className="flex-1 overflow-y-auto px-5 py-8 md:px-10">
          <div className="mx-auto flex max-w-[76ch] flex-col gap-8">
            {search.data ? (
              <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <Label faint>{search.data.result_count} provisions contain the phrase</Label>
                  <button
                    onClick={() => search.clear()}
                    className="font-mono text-[10px] uppercase tracking-[0.24em] text-text-dim transition-colors hover:text-text-ghost"
                  >
                    clear
                  </button>
                </div>
                <ul className="divide-y divide-line-dim border-y border-line-dim">
                  {search.data.items.map((hit) => (
                    <li key={hit.ref} className="py-3">
                      <button
                        onClick={() => {
                          const art = hit.ref.match(/^Article (\S+)/);
                          const rec = hit.ref.match(/^Recital (\d+)/);
                          const anx = hit.ref.match(/^Annex (\S+)/);
                          if (art) openArticle(art[1]);
                          else if (rec) openRecital(Number(rec[1]));
                          else if (anx) openAnnex(anx[1]);
                        }}
                        className="group flex w-full flex-col gap-1 text-left"
                      >
                        <span className="flex items-baseline gap-3">
                          <span className="font-mono text-[11px] text-text-ghost">{hit.ref}</span>
                          {hit.title ? (
                            <span className="font-display text-[11px] text-text-faint">{hit.title}</span>
                          ) : null}
                          <span className="ml-auto font-mono text-[10px] tabular-nums text-text-faint">{hit.matches}×</span>
                        </span>
                        <span className="font-display text-[13px] leading-relaxed text-text-dim transition-opacity group-hover:opacity-60">
                          {hit.excerpt}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {busy ? <Spinner label="loading provision" /> : null}

            {body && !busy ? (
              <article className="rise flex flex-col gap-6">
                <header className="flex flex-col gap-3 border-b border-line-dim pb-5">
                  {showingArticle && location.data ? (
                    <div className="flex flex-wrap items-center gap-2">
                      {location.data.breadcrumb.map((crumb) => (
                        <Badge key={crumb} tone="outline">{crumb}</Badge>
                      ))}
                    </div>
                  ) : null}
                  <Label faint>{body.ref}</Label>
                  <h2 className="font-display text-[clamp(1.35rem,2.2vw,1.85rem)] font-light leading-tight tracking-[-0.02em] text-text-ghost">
                    {body.title ?? body.ref}
                  </h2>
                </header>

                {/* The server renders the provision as Markdown — paragraphs,
                    lettered points and roman sub-points at their real depths. */}
                <div className="prose-act max-w-[76ch]">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {body.markdown ?? body.text}
                  </ReactMarkdown>
                </div>

                {showingArticle && graph.data ? (
                  <CitationNeighbourhood data={graph.data} onOpen={openArticle} />
                ) : null}
              </article>
            ) : null}

            {!body && !busy && !search.data ? (
              <EmptyNote>Pick an entry on the left, or search for a phrase.</EmptyNote>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------------------
   What this provision cites, and what cites it.
--------------------------------------------------------------------------- */
function CitationNeighbourhood({
  data,
  onOpen,
}: {
  data: GraphArticle;
  onOpen: (n: string) => void;
}) {
  const strip = (ref: string) => ref.replace(/^Article /, "");
  return (
    <div className="grid gap-6 border-t border-line-dim pt-6 md:grid-cols-2">
      <div className="flex flex-col gap-3">
        <Label faint>cites</Label>
        {data.cites.length === 0 ? (
          <EmptyNote>Nothing — this provision stands alone.</EmptyNote>
        ) : (
          <ul className="flex flex-wrap gap-2">
            {data.cites.map((r) => (
              <li key={r.ref}>
                <button
                  onClick={() => r.ref.startsWith("Article ") && onOpen(strip(r.ref))}
                  className="transition-opacity hover:opacity-60"
                >
                  <Badge tone="outline">{r.ref} ×{r.count}</Badge>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
      <div className="flex flex-col gap-3">
        <Label faint>cited by</Label>
        {data.cited_by.length === 0 ? (
          <EmptyNote>No provision cites it.</EmptyNote>
        ) : (
          <ul className="flex flex-wrap gap-2">
            {data.cited_by.map((r) => (
              <li key={r.ref}>
                <button onClick={() => onOpen(strip(r.ref))} className="transition-opacity hover:opacity-60">
                  <Badge tone="outline">{r.ref} ×{r.count}</Badge>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
