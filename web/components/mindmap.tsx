"use client";

/**
 * Mindmap — the Act (or a theme in it) as a radial tree.
 *
 * Two sources: the eight curated topic maps, and any single chapter rendered
 * from its own structure.
 */

import { useCallback, useEffect, useState } from "react";

import { api, type MindmapNode } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Mindmap } from "@/components/diagrams";
import { EmptyNote, ErrorNote, Label, Spinner, ViewHeader } from "@/components/shell";

const CHAPTERS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII"];

export function MindmapView({ onOpenArticle }: { onOpenArticle: (n: string) => void }) {
  const topics = useApi(api.mindmaps);
  const topicMap = useApi(api.mindmap);
  const chapterMap = useApi(api.chapterMindmap);

  const [selection, setSelection] = useState<{ kind: "topic" | "chapter"; id: string }>({
    kind: "topic",
    id: "high-risk",
  });

  useEffect(() => {
    void topics.run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [topics.run]);

  const load = useCallback(
    async (next: { kind: "topic" | "chapter"; id: string }) => {
      setSelection(next);
      if (next.kind === "topic") await topicMap.run(next.id);
      else await chapterMap.run(next.id);
    },
    [topicMap, chapterMap]
  );

  useEffect(() => {
    void load({ kind: "topic", id: "high-risk" });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const data: MindmapNode | null = selection.kind === "topic" ? topicMap.data : chapterMap.data;
  const loading = topicMap.loading || chapterMap.loading;
  const error = topicMap.error || chapterMap.error;

  const openRef = (ref: string) => {
    const m = ref.match(/^Article (\S+)/);
    if (m) onOpenArticle(m[1]);
  };

  return (
    <div className="h-full overflow-y-auto px-5 py-8 md:px-8">
      <div className="mx-auto flex max-w-[1000px] flex-col gap-8">
        <ViewHeader
          eyebrow="mindmap"
          title="The Act, as a map"
          lede="Every leaf cites the provision it comes from. Branches come from the Act's own structure and the curated obligation set — nothing here is drawn from outside the text."
        />

        <div className="flex flex-col gap-3">
          <Label faint>themes</Label>
          <div className="flex flex-wrap gap-2">
            {(topics.data?.items ?? []).map((t) => {
              const on = selection.kind === "topic" && selection.id === t.id;
              return (
                <button
                  key={t.id}
                  onClick={() => load({ kind: "topic", id: t.id })}
                  title={t.summary}
                  className={`border px-3 py-1 font-mono text-[10px] uppercase tracking-[0.18em] transition-colors ${
                    on
                      ? "border-text-ghost bg-text-ghost text-bg-void"
                      : "border-line-dim text-text-dim hover:border-line-hi hover:text-text-ghost"
                  }`}
                >
                  {t.title}
                </button>
              );
            })}
          </div>
        </div>

        <div className="flex flex-col gap-3">
          <Label faint>or a single chapter</Label>
          <div className="flex flex-wrap gap-2">
            {CHAPTERS.map((c) => {
              const on = selection.kind === "chapter" && selection.id === c;
              return (
                <button
                  key={c}
                  onClick={() => load({ kind: "chapter", id: c })}
                  className={`border px-3 py-1 font-mono text-[10px] uppercase tracking-[0.18em] transition-colors ${
                    on
                      ? "border-text-ghost bg-text-ghost text-bg-void"
                      : "border-line-dim text-text-dim hover:border-line-hi hover:text-text-ghost"
                  }`}
                >
                  {c}
                </button>
              );
            })}
          </div>
        </div>

        {loading ? <Spinner label="drawing" /> : null}
        {error ? <ErrorNote message={error} /> : null}

        {data ? (
          <div className="flex flex-col gap-5">
            {data.summary ? (
              <p className="max-w-[74ch] font-display text-[14px] leading-relaxed text-text-dim">
                {data.summary}
              </p>
            ) : null}
            <Mindmap node={data} onOpen={openRef} />
          </div>
        ) : !loading && !error ? (
          <EmptyNote>Pick a theme or a chapter.</EmptyNote>
        ) : null}
      </div>
    </div>
  );
}
