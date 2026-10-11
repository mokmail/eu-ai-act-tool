"use client";

import { useCallback, useEffect, useState } from "react";

import { AGENT_URL, useAgui } from "@/lib/agui";
import { api, type Health, type Meta } from "@/lib/api";
import { DashboardView } from "@/components/dashboard";
import { AskView } from "@/components/ask";
import { MapView } from "@/components/map";
import { MindmapView } from "@/components/mindmap";
import { ReferenceView } from "@/components/reference";
import { ClassifyView } from "@/components/classify";
import { CasesView, ProceduresView } from "@/components/guides";
import { ChecklistView } from "@/components/tools";
import { SettingsView } from "@/components/settings";
import { StreamInspector } from "@/components/stream";
import { EMBEDDED, SiteFooter, SiteHeader, SideNav, useMediaQuery, type ViewKey } from "@/components/shell";

export default function Page() {
  const [view, setView] = useState<ViewKey>("overview");
  const [inspecting, setInspecting] = useState(false);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [pendingArticle, setPendingArticle] = useState<string | null>(null);

  // The sidebar is inline on a wide screen and an overlay drawer on a narrow one,
  // so it starts open on one and closed on the other.
  const isDesktop = useMediaQuery("(min-width: 1024px)");
  const [navOpen, setNavOpen] = useState(true);

  useEffect(() => {
    setNavOpen(isDesktop);
  }, [isDesktop]);

  const { turns, running, sources, events, send, stop } = useAgui();

  useEffect(() => {
    api.meta().then(setMeta).catch(() => setMeta(null));
    api.health().then(setHealth).catch(() => setHealth(null));
  }, []);

  /** On a narrow screen every jump should also close the drawer. */
  const closeDrawerIfNarrow = useCallback(() => {
    if (!isDesktop) setNavOpen(false);
  }, [isDesktop]);

  const selectView = useCallback(
    (next: ViewKey) => {
      setView(next);
      closeDrawerIfNarrow();
    },
    [closeDrawerIfNarrow]
  );

  /** Send from anywhere: switch to the Ask view and fire the question. */
  const ask = useCallback(
    (text: string) => {
      setView("ask");
      closeDrawerIfNarrow();
      void send(text);
    },
    [closeDrawerIfNarrow, send]
  );

  /** Open a provision from a diagram, a case or a procedure step. */
  const openArticle = useCallback(
    (number: string) => {
      setPendingArticle(number);
      setView("map");
      closeDrawerIfNarrow();
    },
    [closeDrawerIfNarrow]
  );

  // Which model answers is never surfaced in the chrome — self-hosted deployments
  // configure it in Settings and nothing else needs to know.
  const status = health
    ? health.provider.available
      ? { ok: true, label: "connected" }
      : { ok: false, label: "provider offline" }
    : { ok: null, label: "connecting" };

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader
        view={view}
        onSelect={selectView}
        status={status}
        onInspect={() => setInspecting((prev) => !prev)}
        inspecting={inspecting}
        navOpen={navOpen}
        onToggleNav={() => setNavOpen((prev) => !prev)}
      />

      <div className="mx-auto flex w-full max-w-[1500px] flex-1">
        {/* Wide screen: inline, and collapses to a rail of section numbers. */}
        <aside
          className={`hidden shrink-0 border-r border-line-dim transition-[width] duration-300 ease-out lg:block ${
            // Embedded: this strip's toggle is hidden at lg, so a collapsed rail
            // would be a dead end. Keep it expanded.
            navOpen || EMBEDDED ? "w-[252px] px-6 py-8" : "w-[58px] px-2 py-8"
          }`}
        >
          <SideNav view={view} onSelect={selectView} meta={meta} collapsed={!navOpen && !EMBEDDED} />
        </aside>

        {/* Narrow screen: the same nav, as an overlay drawer. */}
        {navOpen ? (
          <div className="fixed inset-0 z-50 lg:hidden">
            <button
              type="button"
              aria-label="Close navigation"
              onClick={() => setNavOpen(false)}
              className="absolute inset-0 cursor-default bg-bg-void/70 backdrop-blur-sm"
            />
            <aside className="absolute inset-y-0 left-0 w-[286px] overflow-y-auto border-r border-line-dim bg-bg-void px-6 py-8 shadow-2xl">
              <SideNav view={view} onSelect={selectView} meta={meta} />
            </aside>
          </div>
        ) : null}

        <main
          className={`flex min-w-0 flex-1 flex-col ${
            // Embedded, the strip is hidden at lg, so the pane takes the full
            // height there and only subtracts it on the narrower screens where
            // the strip is still drawn.
            EMBEDDED ? "h-[calc(100vh-3rem)] lg:h-screen" : "h-[calc(100vh-4rem)]"
          }`}
        >
          {view === "overview" ? (
            <DashboardView onSelect={selectView} onOpenArticle={openArticle} onAsk={ask} />
          ) : view === "ask" ? (
            <AskView
              turns={turns}
              running={running}
              sources={sources}
              onSend={send}
              onStop={stop}
            />
          ) : view === "map" ? (
            <MapView initialArticle={pendingArticle} />
          ) : view === "mindmap" ? (
            <MindmapView onOpenArticle={openArticle} />
          ) : view === "reference" ? (
            <ReferenceView onAsk={ask} />
          ) : view === "classify" ? (
            <ClassifyView onAsk={ask} />
          ) : view === "procedures" ? (
            <ProceduresView onOpenArticle={openArticle} onAsk={ask} />
          ) : view === "cases" ? (
            <CasesView onOpenArticle={openArticle} onAsk={ask} />
          ) : view === "settings" && !EMBEDDED ? (
            <SettingsView />
          ) : (
            <ChecklistView onAsk={ask} />
          )}
        </main>
      </div>

      {/* Inside kmail.at the host page provides the footer; a second one would
          be a duplicate. */}
      {EMBEDDED ? null : <SiteFooter onSelect={selectView} />}

      <StreamInspector
        events={events}
        endpoint={AGENT_URL}
        open={inspecting}
        onClose={() => setInspecting(false)}
      />
    </div>
  );
}
