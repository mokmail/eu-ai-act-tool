"use client";

/**
 * Hand-rolled visual primitives, in the site's monochrome language.
 *
 * No charting dependency: every diagram is plain SVG or CSS, coloured with
 * Tailwind's `fill-*`, `stroke-*` and `text-*` theme utilities so it follows the
 * light/dark tokens automatically.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { MindmapNode } from "@/lib/api";
import { Label } from "@/components/shell";
import {
  Tooltip,
  ZoomControls,
  humanRelative,
  percent,
  useInView,
  usePanZoom,
  useTooltip,
} from "@/components/viz";

/* ===========================================================================
   Organigram — a top-down tree with elbow connectors.
   Used for the governance structure.
=========================================================================== */
export type OrgNode = {
  name: string;
  ref: string;
  note?: string;
  advisory?: boolean;
  children?: OrgNode[];
};

const BOX_W = 200;
const BOX_H = 58;
const GAP_X = 20;
const GAP_Y = 86;

type Placed = { node: OrgNode; x: number; y: number; depth: number };

function layoutTree(root: OrgNode) {
  const placed: Placed[] = [];
  const links: { x1: number; y1: number; x2: number; y2: number; advisory?: boolean }[] = [];

  // First pass: how wide is each subtree?
  const widths = new Map<OrgNode, number>();
  const measure = (node: OrgNode): number => {
    const kids = node.children ?? [];
    if (!kids.length) {
      widths.set(node, BOX_W);
      return BOX_W;
    }
    const total = kids.reduce((sum, k) => sum + measure(k), 0) + GAP_X * (kids.length - 1);
    const w = Math.max(BOX_W, total);
    widths.set(node, w);
    return w;
  };
  measure(root);

  // Second pass: place parents above the centre of their children.
  const place = (node: OrgNode, left: number, depth: number) => {
    const width = widths.get(node) ?? BOX_W;
    const cx = left + width / 2;
    placed.push({ node, x: cx, y: depth * GAP_Y, depth });
    const kids = node.children ?? [];
    let cursor = left + (width - (kids.reduce((s, k) => s + (widths.get(k) ?? BOX_W), 0) + GAP_X * Math.max(0, kids.length - 1))) / 2;
    for (const kid of kids) {
      const kw = widths.get(kid) ?? BOX_W;
      place(kid, cursor, depth + 1);
      links.push({ x1: cx, y1: depth * GAP_Y, x2: cursor + kw / 2, y2: (depth + 1) * GAP_Y, advisory: kid.advisory });
      cursor += kw + GAP_X;
    }
  };
  place(root, 0, 0);

  const width = widths.get(root) ?? BOX_W;
  const height = (Math.max(...placed.map((p) => p.depth)) + 1) * GAP_Y;
  return { placed, links, width, height };
}

/** Wrap a role name onto at most `maxLines` lines of about `perLine` characters. */
function wrapLabel(text: string, perLine: number, maxLines: number): string[] {
  const words = text.split(/\s+/).filter(Boolean);
  const lines: string[] = [];
  let current = "";
  let consumed = -1;

  for (let i = 0; i < words.length; i++) {
    const candidate = current ? `${current} ${words[i]}` : words[i];
    if (!current || candidate.length <= perLine) {
      current = candidate;
      consumed = i;
    } else {
      lines.push(current);
      current = words[i];
      consumed = i;
      if (lines.length === maxLines) break;
    }
  }
  if (lines.length < maxLines && current) lines.push(current);

  const truncated = consumed < words.length - 1;
  if (truncated && lines.length) {
    const last = lines[lines.length - 1];
    lines[lines.length - 1] = last.length >= perLine ? `${last.slice(0, perLine - 1).trimEnd()}…` : `${last}…`;
  }
  return lines;
}

export function OrgChart({
  root,
  onSelect,
}: {
  root: OrgNode;
  onSelect?: (ref: string) => void;
}) {
  const { placed, links, width, height } = useMemo(() => layoutTree(root), [root]);
  const [hovered, setHovered] = useState<OrgNode | null>(null);
  const { tip, show, hide } = useTooltip();

  // the chain from the root down to each node, so hovering one lights its line of command
  const ancestors = useMemo(() => {
    const map = new Map<OrgNode, Set<OrgNode>>();
    const walk = (node: OrgNode, chain: OrgNode[]) => {
      const here = [...chain, node];
      map.set(node, new Set(here));
      for (const kid of node.children ?? []) walk(kid, here);
    };
    walk(root, []);
    return map;
  }, [root]);

  const litPath = hovered ? ancestors.get(hovered) ?? null : null;

  return (
    <div className="flex flex-col gap-3">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="h-auto w-full"
        role="img"
        aria-label={`Organigram: ${root.name}`}
        onMouseLeave={() => {
          setHovered(null);
          hide();
        }}
      >
        {/* connectors */}
        {links.map((l, i) => {
          const midY = (l.y1 + BOX_H + (l.y2 - l.y1 - BOX_H)) / 2;
          const path = `M ${l.x1} ${l.y1 + BOX_H} L ${l.x1} ${midY} L ${l.x2} ${midY} L ${l.x2} ${l.y2}`;
          // a connector stays lit only when both ends are on the hovered node's chain
          const parent = nodeAt(l.x1, l.y1, placed);
          const child = nodeAt(l.x2, l.y2, placed);
          const lit = litPath !== null && parent !== null && child !== null
            && litPath.has(parent) && litPath.has(child);
          return (
            <path
              key={i}
              d={path}
              fill="none"
              strokeWidth={1}
              strokeDasharray={l.advisory ? "3 3" : undefined}
              className={`stroke-line-hi transition-opacity duration-200 ${
                litPath !== null && !lit ? "opacity-25" : ""
              }`}
            />
          );
        })}

        {/* boxes */}
        {placed.map((p, i) => {
          const on = hovered === p.node;
          const inPath = litPath ? litPath.has(p.node) : true;
          const lines = wrapLabel(p.node.name, 28, 2);
          const isRoot = p.depth === 0;
          const isLevel1 = p.depth === 1;
          const advisory = Boolean(p.node.advisory);

          // three weights of box: the instrument, the bodies, everything below them
          const stroke = isRoot
            ? "stroke-text-ghost"
            : on
              ? "stroke-text-ghost"
              : isLevel1
                ? "stroke-line-hi"
                : "stroke-line-dim";
          const fill = isRoot ? "fill-text-ghost" : on ? "fill-bg-panel" : "fill-none";

          return (
            <g
              key={i}
              transform={`translate(${p.x - BOX_W / 2}, ${p.y})`}
              className={`transition-opacity duration-200 ${inPath ? "opacity-100" : "opacity-30"}`}
              style={{ cursor: "pointer" }}
              role="button"
              tabIndex={0}
              aria-label={`${p.node.name}, ${p.node.ref}${advisory ? ", advisory" : ""}`}
              onMouseEnter={(event) => {
                setHovered(p.node);
                show(p.node.name, `${p.node.ref}${p.node.note ? ` · ${p.node.note}` : ""}`.slice(0, 160), event);
              }}
              onFocus={(event) => {
                const rect = event.currentTarget.getBoundingClientRect();
                setHovered(p.node);
                show(p.node.name, p.node.ref, { clientX: rect.left, clientY: rect.bottom });
              }}
              onBlur={() => {
                setHovered(null);
                hide();
              }}
              onClick={() => onSelect?.(p.node.ref)}
            >
              <rect
                width={BOX_W}
                height={BOX_H}
                strokeWidth={on ? 1.6 : 1}
                strokeDasharray={advisory ? "3 3" : undefined}
                className={`${fill} ${stroke} transition-colors`}
              />

              {/* a heavier spine marks the bodies that sit directly under the instrument */}
              {!isRoot && !advisory ? (
                <rect
                  width={3}
                  height={BOX_H}
                  className={isLevel1 ? "fill-text-ghost" : "fill-line-hi"}
                />
              ) : null}

              {lines.map((line, n) => (
                <text
                  key={n}
                  x={13}
                  y={22 + n * 13}
                  className={isRoot ? "fill-bg-void" : "fill-text-ghost"}
                  style={{ font: "400 11px Inter, sans-serif" }}
                >
                  {line}
                </text>
              ))}

              {/* a rule between the role and its citation, so the two never read as one line */}
              <line
                x1={13}
                x2={BOX_W - 13}
                y1={41}
                y2={41}
                strokeWidth={1}
                className={isRoot ? "stroke-bg-void opacity-30" : "stroke-line-dim"}
              />
              <text
                x={13}
                y={52}
                className={isRoot ? "fill-bg-void opacity-70" : "fill-text-faint"}
                style={{
                  font: "400 8.5px 'JetBrains Mono', monospace",
                  letterSpacing: "0.08em",
                }}
              >
                {p.node.ref}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
        <span className="flex items-center gap-2">
          <span className="inline-block h-[10px] w-[15px] border border-line-hi" aria-hidden />
          <Label faint>institutional — established by the Act</Label>
        </span>
        <span className="flex items-center gap-2">
          <span
            className="inline-block h-[10px] w-[15px] border border-dashed border-line-hi"
            aria-hidden
          />
          <Label faint>advisory</Label>
        </span>
        <Label faint>hover to trace a line of command · click for its provision</Label>
      </div>
      <Tooltip tip={tip} />
    </div>
  );
}

/** The node sitting at a layout coordinate, so a connector can name its two ends. */
function nodeAt(
  x: number,
  y: number,
  placed: { node: OrgNode; x: number; y: number }[]
): OrgNode | null {
  const found = placed.find((p) => Math.abs(p.x - x) < 0.5 && Math.abs(p.y - y) < 0.5);
  return found?.node ?? null;
}

/* ===========================================================================
   Mindmap — radial. Branches around the root; click one to fan out its leaves.
=========================================================================== */
export function Mindmap({ node, onOpen }: { node: MindmapNode; onOpen?: (ref: string) => void }) {
  const [active, setActive] = useState<number | null>(null);
  const [hovered, setHovered] = useState<number | null>(null);
  const { tip, show, hide } = useTooltip();
  const branches = node.children ?? [];

  const size = 760;
  const c = size / 2;
  const ROOT_R = 62;
  const R1 = 176; // the ring the branch pills sit on
  const R2 = 326; // the ring the open branch's leaves reach out to
  const PILL_W = 144;
  const PILL_H = 32;
  // the canvas is wider than the circle: leaf labels are anchored outward and
  // would otherwise be clipped by the viewBox on the left and right
  const PAD_X = 150;

  const angleOf = (i: number, n: number) => (i / Math.max(n, 1)) * Math.PI * 2 - Math.PI / 2;
  const leaves = active !== null ? branches[active].children ?? [] : [];
  const focused = hovered ?? active;

  const title = node.title ?? node.label ?? "";
  const titleLines = wrapLabel(title, 16, 3);
  const clamp = (value: string | undefined, limit: number) =>
    value && value.length > limit ? `${value.slice(0, limit - 1)}…` : value ?? "";

  return (
    <div className="flex flex-col gap-4">
      <svg
        viewBox={`${-PAD_X} 0 ${size + PAD_X * 2} ${size}`}
        className="h-auto w-full max-w-[940px] self-center"
        role="img"
        aria-label={`Mindmap: ${title}`}
        onMouseLeave={() => {
          setHovered(null);
          hide();
        }}
      >
        {/* the two rings the map is built on: branches, then their provisions */}
        <circle
          cx={c}
          cy={c}
          r={R1}
          fill="none"
          strokeWidth={1}
          strokeDasharray="2 5"
          className="stroke-line-dim"
        />
        <circle
          cx={c}
          cy={c}
          r={R2}
          fill="none"
          strokeWidth={1}
          strokeDasharray="2 5"
          className="stroke-line-dim"
        />

        {/* spokes, from the edge of the disc to the pill on the ring */}
        {branches.map((b, i) => {
          const a = angleOf(i, branches.length);
          const on = focused === i;
          return (
            <line
              key={`spoke-${i}`}
              x1={c + Math.cos(a) * (ROOT_R + 3)}
              y1={c + Math.sin(a) * (ROOT_R + 3)}
              x2={c + Math.cos(a) * (R1 - PILL_H / 2 - 3)}
              y2={c + Math.sin(a) * (R1 - PILL_H / 2 - 3)}
              strokeWidth={on ? 1.6 : 1}
              className={`transition-all duration-200 ${on ? "stroke-text-ghost" : "stroke-line-hi"}`}
            />
          );
        })}

        {/* the open branch's provisions, fanned across its own sector of the ring */}
        {active !== null
          ? leaves.map((leaf, j) => {
              const base = angleOf(active, branches.length);
              const spread = Math.min(1.05, 0.22 + leaves.length * 0.11);
              const a =
                leaves.length === 1 ? base : base + (j / (leaves.length - 1) - 0.5) * spread;
              const x = c + Math.cos(a) * R2;
              const y = c + Math.sin(a) * R2;
              const anchor = Math.cos(a) > 0.2 ? "start" : Math.cos(a) < -0.2 ? "end" : "middle";
              const startX = c + Math.cos(base) * (R1 + PILL_H / 2);
              const startY = c + Math.sin(base) * (R1 + PILL_H / 2);
              return (
                <g
                  key={`leaf-${j}`}
                  className="leaf-in"
                  style={{ animationDelay: `${j * 45}ms` }}
                  role="button"
                  tabIndex={0}
                  aria-label={`${leaf.label}, ${leaf.ref}`}
                  onMouseEnter={(event) =>
                    show(
                      leaf.label ?? "",
                      `${leaf.ref}${leaf.note ? ` · ${leaf.note}` : ""}`.slice(0, 160),
                      event
                    )
                  }
                  onClick={() => onOpen?.(leaf.ref)}
                >
                  <path
                    d={`M ${startX} ${startY} Q ${c + Math.cos(a) * ((R1 + R2) / 2)} ${c + Math.sin(base) * ((R1 + R2) / 2)} ${x} ${y}`}
                    fill="none"
                    strokeWidth={1}
                    className="stroke-line-dim"
                  />
                  <circle cx={x} cy={y} r={1.8} className="fill-text-dim" />
                  <text
                    x={x + (anchor === "start" ? 8 : anchor === "end" ? -8 : 0)}
                    y={y + 3}
                    textAnchor={anchor}
                    className="cursor-pointer fill-text-dim transition-colors hover:fill-text-ghost"
                    style={{ font: "400 10px Inter, sans-serif" }}
                  >
                    {clamp(leaf.label, 30)}
                  </text>
                </g>
              );
            })
          : null}

        {/* the instrument itself, inverted so the map has one unambiguous anchor */}
        <circle cx={c} cy={c} r={ROOT_R} className="fill-text-ghost" />
        {titleLines.map((line, i) => (
          <text
            key={i}
            x={c}
            y={c - 8 + i * 15}
            textAnchor="middle"
            className="fill-bg-void"
            style={{ font: "400 12.5px Inter, sans-serif" }}
          >
            {line}
          </text>
        ))}
        <text
          x={c}
          y={c + ROOT_R - 13}
          textAnchor="middle"
          className="fill-bg-void opacity-60"
          style={{ font: "400 8px 'JetBrains Mono', monospace", letterSpacing: "0.14em" }}
        >
          {clamp((node.ref ?? "").toUpperCase(), 20)}
        </text>

        {/* branch pills, each carrying how many provisions sit under it */}
        {branches.map((b, i) => {
          const a = angleOf(i, branches.length);
          const x = c + Math.cos(a) * R1;
          const y = c + Math.sin(a) * R1;
          const on = active === i;
          const dim = focused !== null && focused !== i;
          const count = (b.children ?? []).length;
          return (
            <g
              key={`branch-${i}`}
              transform={`translate(${x - PILL_W / 2}, ${y - PILL_H / 2})`}
              className={`cursor-pointer transition-opacity duration-200 ${
                dim ? "opacity-35" : "opacity-100"
              }`}
              role="button"
              tabIndex={0}
              aria-expanded={on}
              aria-label={`${b.label}, ${count} provisions`}
              onClick={() => setActive(on ? null : i)}
              onMouseEnter={(event) => {
                setHovered(i);
                show(
                  b.label ?? "",
                  `${b.ref}${b.note ? ` · ${b.note}` : ""}`.slice(0, 160),
                  event
                );
              }}
              onMouseLeave={() => setHovered(null)}
              onFocus={() => setHovered(i)}
              onBlur={() => setHovered(null)}
            >
              <rect
                width={PILL_W}
                height={PILL_H}
                strokeWidth={1}
                className={
                  on
                    ? "fill-text-ghost stroke-text-ghost"
                    : "fill-bg-void stroke-line-hi transition-colors"
                }
              />
              <text
                x={11}
                y={20}
                className={on ? "fill-bg-void" : "fill-text-ghost"}
                style={{ font: "400 10.5px Inter, sans-serif" }}
              >
                {clamp(b.label, 18)}
              </text>
              <text
                x={PILL_W - 11}
                y={20}
                textAnchor="end"
                className={on ? "fill-bg-void opacity-70" : "fill-text-faint"}
                style={{ font: "400 8px 'JetBrains Mono', monospace", letterSpacing: "0.08em" }}
              >
                {String(count).padStart(2, "0")}
              </text>
            </g>
          );
        })}
      </svg>

      {active !== null ? (
        <div className="flex flex-col gap-3 border-t border-line-dim pt-4">
          <Label>{branches[active].label}</Label>
          {branches[active].note ? (
            <p className="max-w-[74ch] font-display text-[13px] leading-relaxed text-text-dim">
              {branches[active].note}
            </p>
          ) : null}
          <ul className="flex flex-col divide-y divide-line-dim">
            {(branches[active].children ?? []).map((leaf, j) => (
              <li key={j} className="flex flex-col gap-1 py-3">
                <button
                  onClick={() => onOpen?.(leaf.ref)}
                  className="group flex items-baseline gap-3 text-left transition-opacity hover:opacity-60"
                >
                  <span className="font-display text-[13px] text-text-ghost">{leaf.label}</span>
                  <span className="ml-auto shrink-0 font-mono text-[10px] text-text-faint">{leaf.ref}</span>
                </button>
                {leaf.note ? (
                  <p className="max-w-[74ch] font-display text-[12px] leading-relaxed text-text-faint">
                    {leaf.note}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <Label faint>click a branch to open it</Label>
      )}
      <Tooltip tip={tip} />
    </div>
  );
}

/* ===========================================================================
   Step flow — a numbered vertical procedure.

   Steps open and close: the rail stays scannable while one step at a time can
   be read in full. HTML, not SVG: it is text.
=========================================================================== */
export function StepFlow({
  steps,
  onOpen,
}: {
  steps: { n: number; title: string; detail: string; ref: string }[];
  onOpen?: (ref: string) => void;
}) {
  const { ref, seen } = useInView<HTMLOListElement>();
  const [open, setOpen] = useState<number | null>(() => (steps.length ? steps[0].n : null));

  return (
    <ol
      ref={ref}
      className="relative flex flex-col transition-opacity duration-700"
      style={{ opacity: seen ? 1 : 0 }}
    >
      {steps.map((step, i) => {
        const expanded = open === step.n;
        return (
          <li key={step.n} className="relative flex gap-5 pb-7 last:pb-0">
            {/* the rail */}
            <div className="relative flex flex-col items-center">
              <span
                className={`flex h-[22px] w-[22px] shrink-0 items-center justify-center border font-mono text-[10px] tabular-nums transition-colors ${
                  expanded ? "border-text-ghost text-text-ghost" : "border-line-hi text-text-faint"
                }`}
              >
                {step.n}
              </span>
              {i < steps.length - 1 ? (
                <span className="mt-1 w-px flex-1 bg-line-dim" aria-hidden />
              ) : null}
            </div>

            <div className="flex flex-1 flex-col gap-2 pb-1">
              <button
                type="button"
                onClick={() => setOpen(expanded ? null : step.n)}
                aria-expanded={expanded}
                className="flex items-baseline gap-3 text-left"
              >
                <span
                  className={`font-display text-[15px] leading-snug transition-colors ${
                    expanded ? "text-text-ghost" : "text-text-dim hover:text-text-ghost"
                  }`}
                >
                  {step.title}
                </span>
                <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-text-faint">
                  {expanded ? "−" : "+"}
                </span>
              </button>

              <div
                className="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
                style={{
                  gridTemplateRows: expanded ? "1fr" : "0fr",
                  opacity: expanded ? 1 : 0,
                }}
              >
                <div className="overflow-hidden">
                  <p className="max-w-[74ch] font-display text-[13px] leading-relaxed text-text-dim">
                    {step.detail}
                  </p>
                  <button
                    type="button"
                    onClick={() => onOpen?.(step.ref)}
                    className="mt-2 font-mono text-[10px] uppercase tracking-[0.14em] text-text-faint transition-colors hover:text-text-ghost"
                  >
                    {step.ref} →
                  </button>
                </div>
              </div>
            </div>
          </li>
        );
      })}
    </ol>
  );
}

/* ===========================================================================
   Bar chart — horizontal, monochrome, CSS widths.

   Bars grow from zero when the figure scrolls into view, each row reports its
   share of the total on hover, and a row with a ref is a link to its provision.
=========================================================================== */
export function BarChart({
  data,
  unit = "",
  onSelect,
}: {
  data: { label: string; value: number; ref?: string }[];
  unit?: string;
  onSelect?: (ref: string) => void;
}) {
  const { ref, seen } = useInView<HTMLUListElement>();
  const { tip, show, hide } = useTooltip();
  const [active, setActive] = useState<number | null>(null);

  const max = Math.max(1, ...data.map((d) => d.value));
  const total = data.reduce((sum, d) => sum + d.value, 0);

  const detailOf = (d: { value: number; ref?: string }) =>
    `${d.value.toLocaleString()}${unit} · ${percent(d.value, total)} of the total` +
    (d.ref ? ` · ${d.ref}` : "");

  return (
    <>
      <ul
        ref={ref}
        className="flex flex-col gap-2"
        onMouseLeave={() => {
          setActive(null);
          hide();
        }}
      >
        {data.map((d, i) => {
          const on = active === i;
          return (
            <li key={`${d.label}-${i}`} className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => d.ref && onSelect?.(d.ref)}
                onMouseEnter={(event) => {
                  setActive(i);
                  show(d.label, detailOf(d), event);
                }}
                onFocus={(event) => {
                  const rect = event.currentTarget.getBoundingClientRect();
                  setActive(i);
                  show(d.label, detailOf(d), { clientX: rect.left, clientY: rect.bottom });
                }}
                onBlur={hide}
                className={`w-[190px] shrink-0 truncate text-left font-display text-[12px] transition-colors ${
                  on ? "text-text-ghost" : "text-text-dim"
                }`}
                title={d.label}
              >
                {d.label}
              </button>
              <span className="relative h-[14px] flex-1 bg-bg-panel-hi" aria-hidden>
                <span
                  className={`absolute inset-y-0 left-0 transition-[width,background-color] duration-700 ease-out ${
                    on ? "bg-text-ghost" : "bg-text-dim"
                  }`}
                  style={{ width: `${seen ? Math.max(1.5, (d.value / max) * 100) : 0}%` }}
                />
              </span>
              <span
                className={`w-[64px] shrink-0 text-right font-mono text-[10px] tabular-nums transition-colors ${
                  on ? "text-text-ghost" : "text-text-faint"
                }`}
              >
                {d.value.toLocaleString()}
                {unit}
              </span>
            </li>
          );
        })}
      </ul>
      <Tooltip tip={tip} />
    </>
  );
}

/* ===========================================================================
   Timeline — a proportional axis over a milestone rail.

   A horizontal axis carrying the labels was tried first and abandoned: six
   sentence-length labels collide at any column width narrower than the page.
   So the axis carries only the real spacing — which is the thing a rail cannot
   show, and is why the 2024 cluster reads as a cluster — while the rail carries
   the words. Hovering either one lights the other.
=========================================================================== */
export function TimelineChart({
  events,
  onSelect,
}: {
  events: { date: string; event: string; ref: string }[];
  onSelect?: (ref: string) => void;
}) {
  const { ref, seen } = useInView<HTMLDivElement>();
  const { tip, show, hide } = useTooltip();
  const [active, setActive] = useState<number | null>(null);

  const sorted = useMemo(
    () => [...events].sort((a, b) => a.date.localeCompare(b.date)),
    [events]
  );
  const times = useMemo(() => sorted.map((e) => new Date(e.date).getTime()), [sorted]);

  // All hooks run before the early return: they must fire in the same order every
  // render, so nothing may be computed conditionally above them.
  const min = times.length ? times[0] : 0;
  const max = times.length ? times[times.length - 1] : 0;
  const span = Math.max(1, max - min);
  const at = useCallback((t: number) => ((t - min) / span) * 100, [min, span]);

  const yearMarks = useMemo(() => {
    if (!times.length) return [];
    const marks: { year: number; left: number }[] = [];
    for (let y = new Date(min).getUTCFullYear() + 1; y <= new Date(max).getUTCFullYear(); y++) {
      marks.push({ year: y, left: at(Date.UTC(y, 0, 1)) });
    }
    return marks;
  }, [at, min, max, times.length]);

  if (!sorted.length) return null;

  const now = Date.now();
  const nextIndex = times.findIndex((t) => t > now);

  return (
    <div ref={ref} className="flex flex-col gap-7">
      {/* the axis: real spacing, so the clustering of the 2024 dates is visible */}
      <div className="relative h-[54px] select-none">
        <div className="absolute inset-x-0 top-[26px] h-px bg-line-dim" aria-hidden />
        {yearMarks.map((mark) => (
          <div key={mark.year} className="absolute top-[20px]" style={{ left: `${mark.left}%` }}>
            <span className="block h-[12px] w-px bg-line-hi" aria-hidden />
            <span className="absolute left-0 top-[13px] -translate-x-1/2 font-mono text-[9px] tabular-nums text-text-faint">
              {mark.year}
            </span>
          </div>
        ))}
        {sorted.map((event, i) => {
          const on = active === i;
          const future = i === nextIndex;
          return (
            <button
              key={`tick-${event.date}-${i}`}
              type="button"
              className="absolute top-[17px] -translate-x-1/2 px-[3px] py-1"
              style={{ left: `${at(times[i])}%` }}
              aria-label={`${event.date}: ${event.event}`}
              onMouseEnter={(mouseEvent) => {
                setActive(i);
                show(event.date, `${event.event} · ${humanRelative(event.date)}`, mouseEvent);
              }}
              onMouseLeave={() => {
                setActive(null);
                hide();
              }}
              onFocus={(focusEvent) => {
                const rect = focusEvent.currentTarget.getBoundingClientRect();
                setActive(i);
                show(event.date, `${event.event} · ${humanRelative(event.date)}`, {
                  clientX: rect.left,
                  clientY: rect.bottom,
                });
              }}
              onBlur={hide}
            >
              <span
                className={`block w-[2px] transition-all duration-300 ${
                  on || active === i ? "h-[20px] bg-text-ghost" : "h-[15px]"
                } ${!on && future ? "bg-accent" : !on ? "bg-text-faint" : ""}`}
              />
            </button>
          );
        })}
      </div>

      <ol
        className="flex flex-col transition-[opacity,transform] duration-700 ease-out"
        style={{ opacity: seen ? 1 : 0, transform: seen ? "none" : "translateY(8px)" }}
        onMouseLeave={() => {
          setActive(null);
          hide();
        }}
      >
        {sorted.map((event, i) => {
          const on = active === i;
          const dim = active !== null && !on;
          return (
            <li
              key={`${event.date}-${i}`}
              className={`relative flex gap-5 pb-7 transition-opacity duration-200 last:pb-0 ${
                dim ? "opacity-45" : "opacity-100"
              }`}
              onMouseEnter={(mouseEvent) => {
                setActive(i);
                show(event.date, `${event.event} · ${humanRelative(event.date)}`, mouseEvent);
              }}
            >
              <div className="relative flex flex-col items-center pt-[5px]">
                <span
                  className={`h-[7px] w-[7px] shrink-0 transition-transform duration-200 ${
                    i === nextIndex ? "bg-accent" : "bg-text-ghost"
                  } ${on ? "scale-[1.6]" : ""}`}
                  aria-hidden
                />
                {i < sorted.length - 1 ? (
                  <span className="mt-1 w-px flex-1 bg-line-dim" aria-hidden />
                ) : null}
              </div>
              <div className="flex flex-1 flex-col gap-1">
                <span className="flex items-baseline gap-3">
                  <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-text-ghost">
                    {event.date}
                  </span>
                  {i === nextIndex ? <Label faint>next</Label> : null}
                </span>
                <span className="max-w-[62ch] font-display text-[13px] leading-relaxed text-text-dim">
                  {event.event}
                </span>
                <button
                  type="button"
                  onClick={() => onSelect?.(event.ref)}
                  className="w-fit font-mono text-[10px] uppercase tracking-[0.16em] text-text-faint transition-colors hover:text-text-ghost"
                >
                  {event.ref}
                </button>
              </div>
            </li>
          );
        })}
      </ol>
      <Tooltip tip={tip} />
    </div>
  );
}

/* ===========================================================================
   Citation graph — force-directed, computed once per dataset.
=========================================================================== */
type Vec = { x: number; y: number };

function forceLayout(
  nodes: string[],
  edges: Record<string, Record<string, number>>,
  size: number,
  iterations = 420
): Record<string, Vec> {
  const idx = new Map(nodes.map((n, i) => [n, i]));
  const pos: Vec[] = nodes.map((_, i) => ({
    x: size / 2 + Math.cos((i / nodes.length) * Math.PI * 2) * size * 0.32,
    y: size / 2 + Math.sin((i / nodes.length) * Math.PI * 2) * size * 0.32,
  }));
  const links: [number, number][] = [];
  for (const [from, targets] of Object.entries(edges)) {
    const a = idx.get(from);
    if (a === undefined) continue;
    for (const to of Object.keys(targets)) {
      const b = idx.get(to);
      if (b !== undefined) links.push([a, b]);
    }
  }

  const degree = nodes.map((_, i) => links.filter(([a, b]) => a === i || b === i).length);
  const area = size * size;
  const k = Math.sqrt(area / Math.max(nodes.length, 1)) * 0.62;
  let temp = size * 0.11;

  for (let step = 0; step < iterations; step++) {
    const disp: Vec[] = pos.map(() => ({ x: 0, y: 0 }));

    // repulsion
    for (let i = 0; i < pos.length; i++) {
      for (let j = i + 1; j < pos.length; j++) {
        let dx = pos[i].x - pos[j].x;
        let dy = pos[i].y - pos[j].y;
        let d2 = dx * dx + dy * dy;
        if (d2 < 0.01) {
          dx = (Math.random() - 0.5) * 0.5;
          dy = (Math.random() - 0.5) * 0.5;
          d2 = 0.25;
        }
        const d = Math.sqrt(d2);
        const force = (k * k) / d;
        const fx = (dx / d) * force;
        const fy = (dy / d) * force;
        disp[i].x += fx; disp[i].y += fy;
        disp[j].x -= fx; disp[j].y -= fy;
      }
    }

    // attraction along edges
    for (const [a, b] of links) {
      const dx = pos[a].x - pos[b].x;
      const dy = pos[a].y - pos[b].y;
      const d = Math.max(0.01, Math.hypot(dx, dy));
      const force = (d * d) / k;
      const fx = (dx / d) * force;
      const fy = (dy / d) * force;
      disp[a].x -= fx; disp[a].y -= fy;
      disp[b].x += fx; disp[b].y += fy;
    }

    // gravity toward the centre keeps hubs from drifting to the edge
    for (let i = 0; i < pos.length; i++) {
      const g = 0.012 * (1 + degree[i] * 0.02);
      disp[i].x += (size / 2 - pos[i].x) * g * k * 0.06;
      disp[i].y += (size / 2 - pos[i].y) * g * k * 0.06;
    }

    for (let i = 0; i < pos.length; i++) {
      const d = Math.max(0.01, Math.hypot(disp[i].x, disp[i].y));
      const limited = Math.min(d, temp);
      pos[i].x += (disp[i].x / d) * limited;
      pos[i].y += (disp[i].y / d) * limited;
      pos[i].x = Math.min(size - 24, Math.max(24, pos[i].x));
      pos[i].y = Math.min(size - 24, Math.max(24, pos[i].y));
    }
    temp *= 0.985;
  }

  const out: Record<string, Vec> = {};
  nodes.forEach((n, i) => (out[n] = pos[i]));
  return out;
}

/* ---------------------------------------------------------------------------
   The elastic simulation.

   `forceLayout` runs to convergence once and hands over a good static picture;
   this keeps a live, damped simulation on top of it, so the graph behaves like a
   net rather than a frozen snapshot: drag a node and its neighbours follow on
   their springs, then it settles back. Drag a hub and you feel how much of the
   Act hangs off it.

   The forces are deliberately weak — the seed is already a decent layout, and the
   job here is elasticity, not discovery. Positions live in a ref and a frame tick
   drives the render, because a simulation mutates them sixty times a second.
--------------------------------------------------------------------------- */
const SIM = {
  charge: 900,       // pairwise repulsion
  restLength: 62,    // the length a citation edge wants to be
  stiffness: 0.03,
  gravity: 0.0022,   // pulls the net back from the rim
  damping: 0.7,
  maxSpeed: 10,
};

function useForceSimulation(
  nodes: string[],
  edges: Record<string, Record<string, number>>,
  size: number
) {
  const pad = 28;
  const [, tick] = useState(0);
  const posRef = useRef<Record<string, Vec>>({});
  const velRef = useRef<Record<string, Vec>>({});
  const alphaRef = useRef(0);
  const frameRef = useRef(0);
  const pinnedRef = useRef<string | null>(null);

  const links = useMemo(() => {
    const known = new Set(nodes);
    const out: { a: string; b: string; weight: number }[] = [];
    for (const [from, targets] of Object.entries(edges)) {
      if (!known.has(from)) continue;
      for (const [to, weight] of Object.entries(targets)) {
        if (to !== from && known.has(to)) out.push({ a: from, b: to, weight });
      }
    }
    return out;
  }, [edges, nodes]);

  const step = useCallback(() => {
    const pos = posRef.current;
    const vel = velRef.current;
    const alpha = alphaRef.current;
    if (!nodes.length) return;

    // repulsion between every pair
    for (let i = 0; i < nodes.length; i++) {
      const a = nodes[i];
      const pa = pos[a];
      if (!pa) continue;
      for (let j = i + 1; j < nodes.length; j++) {
        const b = nodes[j];
        const pb = pos[b];
        if (!pb) continue;
        let dx = pa.x - pb.x;
        let dy = pa.y - pb.y;
        let d2 = dx * dx + dy * dy;
        if (d2 < 1) {
          dx = Math.random() - 0.5;
          dy = Math.random() - 0.5;
          d2 = 1;
        }
        const d = Math.sqrt(d2);
        const push = (SIM.charge * alpha) / d2;
        const fx = (dx / d) * push;
        const fy = (dy / d) * push;
        vel[a].x += fx;
        vel[a].y += fy;
        vel[b].x -= fx;
        vel[b].y -= fy;
      }
    }

    // springs along the citation edges
    for (const { a, b } of links) {
      const pa = pos[a];
      const pb = pos[b];
      if (!pa || !pb) continue;
      const dx = pb.x - pa.x;
      const dy = pb.y - pa.y;
      const d = Math.max(0.5, Math.hypot(dx, dy));
      const pull = (d - SIM.restLength) * SIM.stiffness * alpha;
      const fx = (dx / d) * pull;
      const fy = (dy / d) * pull;
      vel[a].x += fx;
      vel[a].y += fy;
      vel[b].x -= fx;
      vel[b].y -= fy;
    }

    // gravity, damping, integration
    for (const name of nodes) {
      const p = pos[name];
      const v = vel[name];
      if (!p || !v) continue;
      if (pinnedRef.current === name) {
        v.x = 0;
        v.y = 0;
        continue; // the pointer owns this one
      }
      v.x += (size / 2 - p.x) * SIM.gravity * alpha;
      v.y += (size / 2 - p.y) * SIM.gravity * alpha;
      v.x *= SIM.damping;
      v.y *= SIM.damping;

      const speed = Math.hypot(v.x, v.y);
      if (speed > SIM.maxSpeed) {
        v.x = (v.x / speed) * SIM.maxSpeed;
        v.y = (v.y / speed) * SIM.maxSpeed;
      }
      p.x += v.x;
      p.y += v.y;

      // a circular bound, not a square one: a square lets edgeless provisions
      // drift into the corners and sit there, marooned
      const ox = p.x - size / 2;
      const oy = p.y - size / 2;
      const radius = Math.hypot(ox, oy);
      const limit = size / 2 - pad;
      if (radius > limit) {
        p.x = size / 2 + (ox / radius) * limit;
        p.y = size / 2 + (oy / radius) * limit;
      }
    }
  }, [links, nodes, size]);

  const run = useCallback(() => {
    if (frameRef.current) return;
    const loop = () => {
      if (pinnedRef.current) alphaRef.current = Math.max(alphaRef.current, 0.6);
      step();
      alphaRef.current *= 0.955;
      tick((n) => (n + 1) % 1_000_000);
      if (alphaRef.current > 0.006 || pinnedRef.current) {
        frameRef.current = requestAnimationFrame(loop);
      } else {
        frameRef.current = 0;
      }
    };
    frameRef.current = requestAnimationFrame(loop);
  }, [step]);

  // seed from the converged layout, then let it breathe very briefly
  useEffect(() => {
    posRef.current = forceLayout(nodes, edges, size);
    velRef.current = Object.fromEntries(nodes.map((n) => [n, { x: 0, y: 0 }]));
    alphaRef.current = 0.5;
    run();
    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
      frameRef.current = 0;
    };
  }, [nodes, edges, size, run]);

  const reheat = useCallback(
    (alpha = 0.6) => {
      alphaRef.current = Math.max(alphaRef.current, alpha);
      run();
    },
    [run]
  );

  const beginDrag = useCallback(
    (name: string) => {
      pinnedRef.current = name;
      reheat(0.85);
    },
    [reheat]
  );

  const moveDrag = useCallback(
    (name: string, point: Vec) => {
      posRef.current[name] = point;
      reheat(0.85);
    },
    [reheat]
  );

  const endDrag = useCallback(() => {
    pinnedRef.current = null;
    reheat(0.5);
  }, [reheat]);

  return { positions: posRef.current, beginDrag, moveDrag, endDrag, reheat };
}

export function CitationGraph({
  nodes,
  edges,
  onSelect,
}: {
  nodes: string[];
  edges: Record<string, Record<string, number>>;
  onSelect?: (ref: string) => void;
}) {
  const size = 760;
  const [hover, setHover] = useState<string | null>(null);
  const [focus, setFocus] = useState<string | null>(null);
  const [hubsOnly, setHubsOnly] = useState(false);
  const [dragging, setDragging] = useState<string | null>(null);
  const { tip, show, hide } = useTooltip();
  const panZoom = usePanZoom(size);

  // a drag must not also count as a click on whatever is underneath it
  const downAt = useRef<{ x: number; y: number } | null>(null);
  const dragged = useRef(false);
  const dragNode = useRef<string | null>(null);

  // live positions, elastic under the pointer
  const { positions, beginDrag, moveDrag, endDrag, reheat } = useForceSimulation(
    nodes,
    edges,
    size
  );

  const { indegree, outdegree } = useMemo(() => {
    const incoming: Record<string, number> = {};
    const outgoing: Record<string, number> = {};
    for (const [from, targets] of Object.entries(edges)) {
      outgoing[from] = (outgoing[from] ?? 0) + Object.keys(targets).length;
      for (const to of Object.keys(targets)) incoming[to] = (incoming[to] ?? 0) + 1;
    }
    return { indegree: incoming, outdegree: outgoing };
  }, [edges]);

  const hubThreshold = useMemo(
    () => Math.max(6, Math.round(Math.sqrt(nodes.length) * 1.6)),
    [nodes.length]
  );
  const isHub = (n: string) => (indegree[n] ?? 0) >= hubThreshold;

  const visible = useMemo(
    () => (hubsOnly ? new Set(nodes.filter(isHub)) : null),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [hubsOnly, nodes, indegree, hubThreshold]
  );

  const neighbours = useMemo(() => {
    if (!focus) return null;
    const set = new Set<string>([focus]);
    for (const to of Object.keys(edges[focus] ?? {})) set.add(to);
    for (const [from, targets] of Object.entries(edges)) {
      if (targets[focus]) set.add(from);
    }
    return set;
  }, [edges, focus]);

  const radius = (n: string) => 3 + Math.min(9, Math.sqrt(indegree[n] ?? 0) * 2.1);
  const active = dragging ?? focus ?? hover;
  const shownNodes = visible ? nodes.filter((n) => visible.has(n)) : nodes;

  const detailOf = (n: string) => {
    const cited = indegree[n] ?? 0;
    const cites = outdegree[n] ?? 0;
    return `${cited} incoming · ${cites} outgoing${
      isHub(n) ? ` · a hub (≥${hubThreshold} incoming)` : ""
    }`;
  };

  return (
    <div className="flex flex-col gap-3">
      <svg
        viewBox={panZoom.viewBox}
        className="h-auto w-full touch-none"
        role="img"
        aria-label="Citation graph between provisions"
        style={{ cursor: panZoom.zoom > 1 ? (panZoom.panning ? "grabbing" : "grab") : "default" }}
        onWheel={panZoom.onWheel}
        onPointerDown={(event) => {
          downAt.current = { x: event.clientX, y: event.clientY };
          dragged.current = false;
          panZoom.onPointerDown(event);
        }}
        onPointerMove={(event) => {
          if (
            downAt.current &&
            Math.hypot(event.clientX - downAt.current.x, event.clientY - downAt.current.y) > 3
          ) {
            dragged.current = true;
          }
          panZoom.onPointerMove(event);
        }}
        onPointerUp={(event) => {
          panZoom.onPointerUp(event);
          // the click event fires right after pointerup; clear afterwards
          window.setTimeout(() => {
            dragged.current = false;
          }, 0);
        }}
      >
        <g className="stroke-line-hi">
          {Object.entries(edges).map(([from, targets]) =>
            Object.entries(targets).map(([to, weight]) => {
              const a = positions[from];
              const b = positions[to];
              if (!a || !b) return null;
              if (visible && !(visible.has(from) && visible.has(to))) return null;
              const dim = active && neighbours && !(active === from || active === to);
              const dx = b.x - a.x;
              const dy = b.y - a.y;
              const d = Math.max(1, Math.hypot(dx, dy));
              // bow each link so parallel citations fan apart and the net reads elastic
              const bow =
                Math.min(22, d * 0.12) * ((from.length + to.length) % 2 === 0 ? 1 : -1);
              const mx = (a.x + b.x) / 2 - (dy / d) * bow;
              const my = (a.y + b.y) / 2 + (dx / d) * bow;
              return (
                <path
                  key={`${from}->${to}`}
                  d={`M ${a.x} ${a.y} Q ${mx} ${my} ${b.x} ${b.y}`}
                  fill="none"
                  strokeWidth={0.4 + Math.min(1.3, (weight ?? 1) * 0.3)}
                  opacity={dim ? 0.1 : 0.5}
                />
              );
            })
          )}
        </g>
        {shownNodes.map((n) => {
          const p = positions[n];
          if (!p) return null;
          const dim = active && neighbours && !neighbours.has(n);
          const isActive = active === n;
          return (
            <g key={n}>
              <circle
                cx={p.x}
                cy={p.y}
                r={isActive ? radius(n) + 1.5 : radius(n)}
                className={
                  isActive
                    ? "fill-text-ghost"
                    : dim
                      ? "fill-text-faint opacity-25"
                      : "fill-text-dim"
                }
                style={{ cursor: dragging === n ? "grabbing" : "grab", touchAction: "none" }}
                onMouseEnter={(event) => {
                  if (dragNode.current) return;
                  setHover(n);
                  show(n, detailOf(n), event);
                }}
                onMouseLeave={() => {
                  setHover(null);
                  hide();
                }}
                onPointerDown={(event) => {
                  // the pointer owns the node: no panning, no click-through to empty space
                  event.stopPropagation();
                  event.currentTarget.setPointerCapture?.(event.pointerId);
                  dragNode.current = n;
                  downAt.current = { x: event.clientX, y: event.clientY };
                  dragged.current = false;
                  setDragging(n);
                  beginDrag(n);
                }}
                onPointerMove={(event) => {
                  if (dragNode.current !== n) return;
                  const start = downAt.current;
                  if (start && Math.hypot(event.clientX - start.x, event.clientY - start.y) > 3) {
                    dragged.current = true;
                  }
                  const svg = event.currentTarget.ownerSVGElement;
                  if (!svg) return;
                  moveDrag(
                    n,
                    panZoom.toUser(event.clientX, event.clientY, svg.getBoundingClientRect())
                  );
                }}
                onPointerUp={() => {
                  if (dragNode.current !== n) return;
                  dragNode.current = null;
                  endDrag();
                  setDragging(null);
                  window.setTimeout(() => {
                    dragged.current = false;
                  }, 0);
                }}
                onPointerCancel={() => {
                  if (dragNode.current !== n) return;
                  dragNode.current = null;
                  endDrag();
                  setDragging(null);
                }}
                onClick={() => {
                  if (dragged.current) return;
                  setFocus(isActive ? null : n);
                  onSelect?.(n);
                }}
              />
              {(isActive || ((indegree[n] ?? 0) > 12 && !dim)) ? (
                <text
                  x={p.x + radius(n) + 4}
                  y={p.y + 3}
                  className="fill-text-ghost"
                  style={{ font: "400 8.5px 'JetBrains Mono', monospace" }}
                >
                  {n.replace("Article ", "Art ")}
                </text>
              ) : null}
            </g>
          );
        })}
      </svg>

      <div className="flex flex-wrap items-center justify-between gap-4">
        <Label faint>
          drag a node to pull the net · node size = how often it is cited
        </Label>
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={() => setHubsOnly((prev) => !prev)}
            aria-pressed={hubsOnly}
            className={`border px-2 py-1 font-mono text-[10px] uppercase tracking-[0.18em] transition-colors ${
              hubsOnly
                ? "border-text-ghost text-text-ghost"
                : "border-line-dim text-text-dim hover:border-line-hi hover:text-text-ghost"
            }`}
          >
            {hubsOnly ? "all provisions" : `hubs only (${hubThreshold}+)`}
          </button>
          <button
            type="button"
            onClick={() => reheat(1)}
            className="border border-line-dim px-2 py-1 font-mono text-[10px] uppercase tracking-[0.18em] text-text-dim transition-colors hover:border-line-hi hover:text-text-ghost"
          >
            shake
          </button>
          {focus ? (
            <button
              type="button"
              onClick={() => setFocus(null)}
              className="font-mono text-[10px] uppercase tracking-[0.24em] text-text-dim transition-colors hover:text-text-ghost"
            >
              clear {focus}
            </button>
          ) : (
            <Label faint>click to isolate · scroll to zoom</Label>
          )}
          <ZoomControls panZoom={panZoom} />
        </div>
      </div>
      <Tooltip tip={tip} />
    </div>
  );
}
