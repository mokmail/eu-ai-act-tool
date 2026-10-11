"use client";

import { useEffect, useState } from "react";

/* ---------------------------------------------------------------------------
   Primitives — the kmail.at editorial language: hairline rules, 10px mono
   labels with wide tracking, monochrome everything.
--------------------------------------------------------------------------- */

export function Label({
  children,
  faint,
  className = "",
}: {
  children: React.ReactNode;
  faint?: boolean;
  className?: string;
}) {
  return (
    <span className={`label-caps ${faint ? "label-caps--faint" : ""} ${className}`}>
      {children}
    </span>
  );
}

export function Panel({
  children,
  className = "",
  as: Tag = "div",
}: {
  children: React.ReactNode;
  className?: string;
  as?: React.ElementType;
}) {
  return (
    <Tag className={`border border-line-dim bg-bg-panel ${className}`}>{children}</Tag>
  );
}

export function Spinner({ label }: { label?: string }) {
  return (
    <span className="inline-flex items-center gap-2">
      <span className="pulse-line inline-block h-[7px] w-[7px] bg-text-ghost" />
      {label ? <Label faint>{label}</Label> : null}
    </span>
  );
}

export function Badge({
  children,
  tone = "dim",
}: {
  children: React.ReactNode;
  tone?: "dim" | "ghost" | "outline";
}) {
  const cls =
    tone === "ghost"
      ? "bg-text-ghost text-bg-void border-text-ghost"
      : tone === "outline"
        ? "border-line-hi text-text-ghost"
        : "border-line-dim text-text-dim";
  return (
    <span
      className={`inline-flex items-center border px-2 py-[3px] font-mono text-[10px] uppercase tracking-[0.16em] ${cls}`}
    >
      {children}
    </span>
  );
}

export function StatusDot({ ok, label }: { ok: boolean | null; label: string }) {
  const tone =
    ok === null ? "bg-text-faint" : ok ? "bg-text-ghost" : "bg-text-faint";
  return (
    <span className="inline-flex items-center gap-2" title={label}>
      <span
        className={`inline-block h-[6px] w-[6px] ${tone} ${ok ? "pulse-line" : ""}`}
      />
      <Label faint>{label}</Label>
    </span>
  );
}

export function Spinner_text() {
  return <span className="pulse-line">▍</span>;
}

/* ---------------------------------------------------------------------------
   Embedded mode

   kmail.at serves this app at /tools/eu-ai-act/app inside its own page, so the
   host already provides the masthead, the footer and the theme control. In that
   shape the app drops its duplicate branding, and the provider settings are not
   listed at all — a public deployment has no business exposing them.
--------------------------------------------------------------------------- */
export const EMBEDDED = process.env.NEXT_PUBLIC_EMBEDDED === "1";

/* ---------------------------------------------------------------------------
   Theme toggle — shares kmail.at's localStorage key, so an embedded app follows
   the host page's theme instead of fighting it.
--------------------------------------------------------------------------- */
export function ThemeToggle() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    setDark(document.documentElement.classList.contains("dark"));
  }, []);

  const toggle = () => {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    try {
      localStorage.setItem("kmail-theme", next ? "dark" : "light");
    } catch {
      /* private mode */
    }
  };

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
      title={dark ? "light" : "dark"}
      className="flex h-8 w-8 items-center justify-center rounded-full border border-line-dim text-text-dim transition-colors hover:border-line-hi hover:text-text-ghost"
    >
      {dark ? (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden>
          <circle cx="12" cy="12" r="4.1" />
          <path d="M12 2.6v2.1M12 19.3v2.1M4.2 4.2l1.5 1.5M18.3 18.3l1.5 1.5M2.6 12h2.1M19.3 12h2.1M4.2 19.8l1.5-1.5M18.3 5.7l1.5-1.5" />
        </svg>
      ) : (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden>
          <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
        </svg>
      )}
    </button>
  );
}

/* ---------------------------------------------------------------------------
   Header — the kmail.at masthead: a drawer toggle, the logo mark and mono
   wordmark, then the round controls.

   The centred nav that used to sit here listed the same views as the sidebar, so
   it is gone: navigation lives in one place, and the sidebar collapses.
--------------------------------------------------------------------------- */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const list = window.matchMedia(query);
    const update = () => setMatches(list.matches);
    update();
    list.addEventListener("change", update);
    return () => list.removeEventListener("change", update);
  }, [query]);

  return matches;
}

export function SiteHeader({
  view,
  onSelect,
  status,
  onInspect,
  inspecting,
  navOpen,
  onToggleNav,
}: {
  view: ViewKey;
  onSelect: (v: ViewKey) => void;
  status: { ok: boolean | null; label: string };
  onInspect: () => void;
  inspecting: boolean;
  navOpen: boolean;
  onToggleNav: () => void;
}) {
  return (
    <header className="sticky top-0 z-40 isolate border-b border-line-dim bg-bg-void/85 backdrop-blur-md">
      <div
        className={`mx-auto flex max-w-[1500px] items-center justify-between px-5 md:px-10 ${
          EMBEDDED ? "h-12" : "h-16"
        }`}
      >
        <div className="flex min-w-0 items-center gap-3">
          <button
            type="button"
            onClick={onToggleNav}
            aria-label={navOpen ? "Collapse navigation" : "Expand navigation"}
            aria-expanded={navOpen}
            title={navOpen ? "collapse navigation" : "expand navigation"}
            className="flex h-8 w-8 shrink-0 items-center justify-center border border-line-dim text-text-dim transition-colors hover:border-line-hi hover:text-text-ghost"
          >
            <span className="flex flex-col gap-[3px]" aria-hidden>
              <span className="block h-px w-[13px] bg-current" />
              <span className="block h-px w-[13px] bg-current" />
              <span className="block h-px w-[13px] bg-current" />
            </span>
          </button>

          {EMBEDDED ? (
            // The host page already carries the kmail.at masthead. Repeating the
            // logo and wordmark here would read as a second site inside the first.
            <button
              type="button"
              onClick={() => onSelect("overview")}
              className="min-w-0 truncate font-mono text-[10px] uppercase tracking-[0.28em] text-text-dim transition-colors hover:text-text-ghost"
            >
              eu ai act
            </button>
          ) : (
          <button
            type="button"
            onClick={() => onSelect("overview")}
            className="group flex min-w-0 shrink items-center gap-2.5"
            aria-label="kmail.at — EU AI Act"
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/logo-mark.png"
              alt=""
              width={24}
              height={24}
              className="h-6 w-6 object-contain grayscale transition-all duration-500 group-hover:grayscale-0"
            />
            <span className="font-mono text-[11px] font-medium uppercase tracking-[0.28em] text-text-ghost">
              kmail.at
            </span>
            <span className="mx-1 hidden h-4 w-px bg-line-dim sm:block" aria-hidden />
            <span className="hidden font-mono text-[10px] uppercase tracking-[0.28em] text-text-dim sm:block">
              eu ai act
            </span>
          </button>
          )}
        </div>

        <div className="flex items-center gap-3 sm:gap-4">
          <StatusDot ok={status.ok} label={status.label} />
          <button
            onClick={onInspect}
            className={`hidden font-mono text-[10px] uppercase tracking-[0.28em] transition-colors sm:inline ${
              inspecting ? "text-text-ghost" : "text-text-dim hover:text-text-ghost"
            }`}
          >
            {inspecting ? "stream ▾" : "stream ▸"}
          </button>
          {EMBEDDED ? null : (
          <>
          <button
            type="button"
            onClick={() => onSelect("settings")}
            aria-label="AI provider settings"
            title="settings"
            className={`flex h-8 w-8 items-center justify-center rounded-full border transition-colors ${
              view === "settings"
                ? "border-line-hi text-text-ghost"
                : "border-line-dim text-text-dim hover:border-line-hi hover:text-text-ghost"
            }`}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden>
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1A1.7 1.7 0 0 0 9 19.4a1.7 1.7 0 0 0-1.9.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1A1.7 1.7 0 0 0 4.6 9a1.7 1.7 0 0 0-.3-1.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.9.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.9V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z" />
            </svg>
          </button>
          <ThemeToggle />
          </>
          )}
        </div>
      </div>
    </header>
  );
}

/* ---------------------------------------------------------------------------
   Footer — kmail.at's four-column footer, in this app's terms.
--------------------------------------------------------------------------- */
export function SiteFooter({ onSelect }: { onSelect: (v: ViewKey) => void }) {
  return (
    <footer className="mt-32 border-t border-line-dim">
      <div className="mx-auto max-w-[1500px] px-5 py-16 md:px-10">
        <div className="grid gap-12 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <p className="flex items-center gap-2.5">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/logo-mark.png"
                alt=""
                width={26}
                height={26}
                className="h-[26px] w-[26px] object-contain"
              />
              <span className="font-mono text-[11px] font-medium uppercase tracking-[0.28em] text-text-ghost">
                kmail.at
              </span>
            </p>
            <p className="mt-5 max-w-[30ch] text-[13px] font-light leading-relaxed text-text-dim">
              A navigator for Regulation (EU) 2024/1689 — the text, the obligations,
              the procedures and the cases, with every claim cited.
            </p>
          </div>

          <div>
            <p className="label-caps">read</p>
            <ul className="mt-5 space-y-3 font-mono text-[11px] uppercase tracking-[0.2em]">
              {(["overview", "map", "mindmap", "reference"] as ViewKey[]).map((key) => (
                <li key={key}>
                  <button
                    onClick={() => onSelect(key)}
                    className="text-text-dim transition-colors hover:text-text-ghost"
                  >
                    {key}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <p className="label-caps">apply</p>
            <ul className="mt-5 space-y-3 font-mono text-[11px] uppercase tracking-[0.2em]">
              {(["classify", "procedures", "cases", "comply"] as ViewKey[]).map((key) => (
                <li key={key}>
                  <button
                    onClick={() => onSelect(key)}
                    className="text-text-dim transition-colors hover:text-text-ghost"
                  >
                    {key}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <p className="label-caps">elsewhere</p>
            <ul className="mt-5 space-y-3 font-mono text-[11px] uppercase tracking-[0.2em]">
              <li>
                <a
                  href="https://kmail.at"
                  target="_blank"
                  rel="noopener"
                  className="text-text-dim hover:text-text-ghost"
                >
                  kmail.at
                </a>
              </li>
              <li>
                <a
                  href="https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32024R1689"
                  target="_blank"
                  rel="noopener"
                  className="text-text-dim hover:text-text-ghost"
                >
                  eur-lex
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/mokmail"
                  target="_blank"
                  rel="noopener"
                  className="text-text-dim hover:text-text-ghost"
                >
                  github
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-16 flex flex-col gap-3 border-t border-line-dim pt-8 md:flex-row md:items-center md:justify-between">
          <p className="font-mono text-[10px] uppercase tracking-[0.24em] text-text-faint">
            © 2026 Mohammed Kmail · Vienna, AT
          </p>
          <p className="font-mono text-[10px] uppercase tracking-[0.24em] text-text-faint">
            Built on the official EUR-Lex text · a compliance aid, not legal advice
          </p>
        </div>
      </div>
    </footer>
  );
}

/* ---------------------------------------------------------------------------
   Side navigation
--------------------------------------------------------------------------- */
export type ViewKey =
  | "overview"
  | "ask"
  | "map"
  | "mindmap"
  | "reference"
  | "classify"
  | "procedures"
  | "cases"
  | "comply"
  | "settings";

export type ViewItem = { key: ViewKey; label: string; hint: string };

/**
 * The nav is grouped the way the work actually splits: understand the Act, then
 * apply it.
 *
 * Charts used to be a separate destination listing the same numbers the dashboard
 * drew; it is folded into the dashboard's tabs, so it is not listed here.
 */
export const VIEW_GROUPS: { group: string; items: ViewItem[] }[] = [
  {
    group: "Understand",
    items: [
      { key: "overview", label: "Overview", hint: "The dashboard — figures, charts, graphs" },
      { key: "ask", label: "Ask", hint: "Natural language, grounded in the Act" },
      { key: "map", label: "Map", hint: "Navigate its own structure" },
      { key: "mindmap", label: "Mindmap", hint: "Themes as a radial map" },
      { key: "reference", label: "Reference", hint: "Timeline, penalties, definitions" },
    ],
  },
  {
    group: "Apply",
    items: [
      { key: "classify", label: "Classify", hint: "Walk the classification ladder" },
      { key: "procedures", label: "Procedures", hint: "What to do, in order" },
      { key: "cases", label: "Cases", hint: "Worked examples" },
      { key: "comply", label: "Comply", hint: "Obligation checklists" },
    ],
  },
  // Configuring the model provider is an operator's job, not a visitor's. On a
  // public deployment the group is absent from the nav entirely, and page.tsx
  // refuses the view even if it is asked for directly.
  ...(EMBEDDED
    ? []
    : [
        {
          group: "System",
          items: [{ key: "settings" as ViewKey, label: "Settings", hint: "Your own AI provider" }],
        },
      ]),
];

export const VIEWS: ViewItem[] = VIEW_GROUPS.flatMap((g) => g.items);

export function SideNav({
  view,
  onSelect,
  meta,
  collapsed = false,
}: {
  view: ViewKey;
  onSelect: (v: ViewKey) => void;
  meta: { counts: { articles: number; recitals: number; annexes: number } } | null;
  collapsed?: boolean;
}) {
  // Numbered once, up front, so the rail and the full list always agree.
  const indexOf = new Map(VIEWS.map((item, i) => [item.key, i + 1]));

  if (collapsed) {
    return (
      <nav className="flex flex-col gap-5" aria-label="Sections">
        {VIEW_GROUPS.map((group) => (
          <div key={group.group} className="flex flex-col items-center gap-1">
            <span className="mb-1 h-px w-4 bg-line-dim" aria-hidden title={group.group} />
            {group.items.map((item) => {
              const active = item.key === view;
              return (
                <button
                  key={item.key}
                  onClick={() => onSelect(item.key)}
                  title={`${item.label} — ${item.hint}`}
                  aria-label={`${item.label}: ${item.hint}`}
                  aria-current={active ? "page" : undefined}
                  className={`flex h-7 w-full items-center justify-center border-l font-mono text-[10px] tabular-nums transition-colors ${
                    active
                      ? "border-text-ghost text-text-ghost"
                      : "border-line-dim text-text-faint hover:border-line-hi hover:text-text-ghost"
                  }`}
                >
                  {String(indexOf.get(item.key)).padStart(2, "0")}
                </button>
              );
            })}
          </div>
        ))}
      </nav>
    );
  }

  return (
    <nav className="flex flex-col gap-7" aria-label="Sections">
      {VIEW_GROUPS.map((group) => (
        <div key={group.group} className="flex flex-col gap-1">
          <Label faint className="mb-2 block">{group.group}</Label>
          {group.items.map((item) => {
            const active = item.key === view;
            return (
              <button
                key={item.key}
                onClick={() => onSelect(item.key)}
                aria-current={active ? "page" : undefined}
                className={`group flex items-baseline gap-3 border-l px-3 py-2 text-left transition-colors ${
                  active
                    ? "border-text-ghost text-text-ghost"
                    : "border-line-dim text-text-dim hover:border-line-hi hover:text-text-ghost"
                }`}
              >
                <span className="font-mono text-[10px] tabular-nums opacity-50">
                  {String(indexOf.get(item.key)).padStart(2, "0")}
                </span>
                <span className="flex flex-col gap-[3px]">
                  <span className="font-mono text-[10px] uppercase tracking-[0.24em]">
                    {item.label}
                  </span>
                  <span className="font-display text-[11px] leading-tight text-text-faint">
                    {item.hint}
                  </span>
                </span>
              </button>
            );
          })}
        </div>
      ))}

      {meta ? (
        <div className="flex flex-col gap-3 border-t border-line-dim pt-5">
          <Label faint>Corpus</Label>
          <dl className="flex flex-col gap-[6px] font-mono text-[10px] tabular-nums text-text-dim">
            <div className="flex justify-between">
              <dt>Articles</dt>
              <dd className="text-text-ghost">{meta.counts.articles}</dd>
            </div>
            <div className="flex justify-between">
              <dt>Recitals</dt>
              <dd className="text-text-ghost">{meta.counts.recitals}</dd>
            </div>
            <div className="flex justify-between">
              <dt>Annexes</dt>
              <dd className="text-text-ghost">{meta.counts.annexes}</dd>
            </div>
          </dl>
          <p className="font-display text-[11px] leading-relaxed text-text-faint">
            Full text from EUR-Lex. A compliance aid — not legal advice.
          </p>
        </div>
      ) : null}
    </nav>
  );
}

/* ---------------------------------------------------------------------------
   Shared view furniture
--------------------------------------------------------------------------- */
export function ViewHeader({
  eyebrow,
  title,
  lede,
}: {
  eyebrow: string;
  title: string;
  lede?: string;
}) {
  return (
    <div className="flex flex-col gap-3 border-b border-line-dim pb-6">
      <Label faint>{eyebrow}</Label>
      <h1 className="font-display text-[clamp(1.75rem,3vw,2.5rem)] font-light leading-[1.1] tracking-[-0.02em] text-text-ghost">
        {title}
      </h1>
      {lede ? (
        <p className="max-w-[62ch] font-display text-[15px] leading-relaxed text-text-dim">
          {lede}
        </p>
      ) : null}
    </div>
  );
}

export function ErrorNote({ message }: { message: string }) {
  return (
    <Panel className="flex items-baseline gap-3 border-line-hi px-4 py-3">
      <Label faint>error</Label>
      <span className="font-display text-[13px] leading-relaxed text-text-ghost">
        {message}
      </span>
    </Panel>
  );
}

export function EmptyNote({ children }: { children: React.ReactNode }) {
  return (
    <p className="font-display text-[13px] leading-relaxed text-text-faint">{children}</p>
  );
}
