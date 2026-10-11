"use client";

/**
 * Interaction primitives for the diagrams.
 *
 * The charts are hand-rolled SVG/CSS, so the interactivity is too — kept here
 * rather than repeated in every figure:
 *
 *   useTooltip / <Tooltip>   hover readouts, positioned `fixed` so they escape
 *                            the dashboard's own scroll container
 *   useInView                start an animation only once a figure is on screen
 *   useCountUp               numbers that count up as the figure appears
 *   useDragPan               wheel-zoom and drag-pan for the big SVG canvases
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

/* --------------------------------------------------------------------------
   Tooltip
-------------------------------------------------------------------------- */
export type Tip = { title: string; detail?: string; x: number; y: number } | null;

export type TipState = {
  tip: Tip;
  show: (title: string, detail: string | undefined, event: { clientX: number; clientY: number }) => void;
  hide: () => void;
};

export function useTooltip(): TipState {
  const [tip, setTip] = useState<Tip>(null);

  const show = useCallback(
    (title: string, detail: string | undefined, event: { clientX: number; clientY: number }) => {
      setTip({ title, detail, x: event.clientX, y: event.clientY });
    },
    []
  );
  const hide = useCallback(() => setTip(null), []);

  return useMemo(() => ({ tip, show, hide }), [tip, show, hide]);
}

export function Tooltip({ tip }: { tip: Tip }) {
  if (!tip) return null;

  // keep the readout inside the viewport near the right and bottom edges
  const flipX = typeof window !== "undefined" && tip.x > window.innerWidth - 260;
  const flipY = typeof window !== "undefined" && tip.y > window.innerHeight - 96;

  return (
    <div
      className="pointer-events-none fixed z-[60] max-w-[248px] border border-line-hi bg-bg-void/95 px-2.5 py-1.5 backdrop-blur-md"
      style={{
        left: tip.x + (flipX ? -12 : 14),
        top: tip.y + (flipY ? -46 : 16),
        transform: flipX ? "translateX(-100%)" : undefined,
      }}
      role="status"
    >
      <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-text-ghost">
        {tip.title}
      </p>
      {tip.detail ? (
        <p className="mt-1 font-display text-[11px] leading-snug text-text-dim">{tip.detail}</p>
      ) : null}
    </div>
  );
}

/* --------------------------------------------------------------------------
   Animation helpers
-------------------------------------------------------------------------- */
export function useInView<T extends HTMLElement>(rootMargin = "0px 0px -8% 0px") {
  const ref = useRef<T | null>(null);
  const [seen, setSeen] = useState(false);

  useEffect(() => {
    const element = ref.current;
    if (!element || seen) return;
    if (typeof IntersectionObserver === "undefined") {
      setSeen(true);
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setSeen(true);
          observer.disconnect();
        }
      },
      { rootMargin }
    );
    observer.observe(element);
    return () => observer.disconnect();
  }, [rootMargin, seen]);

  return { ref, seen };
}

/** A number that eases up to `target` once `active` turns true. */
export function useCountUp(target: number, active: boolean, duration = 760): number {
  const [value, setValue] = useState(active ? target : 0);

  useEffect(() => {
    if (!active) return;
    if (typeof requestAnimationFrame === "undefined") {
      setValue(target);
      return;
    }
    let frame = 0;
    const started = performance.now();
    const step = (now: number) => {
      const t = Math.min(1, (now - started) / duration);
      setValue(Math.round(target * (1 - Math.pow(1 - t, 3))));
      if (t < 1) frame = requestAnimationFrame(step);
    };
    frame = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frame);
  }, [target, active, duration]);

  return value;
}

/* --------------------------------------------------------------------------
   Zoom and pan for the SVG canvases
-------------------------------------------------------------------------- */
export type PanZoom = {
  viewBox: string;
  zoom: number;
  onWheel: (event: React.WheelEvent) => void;
  onPointerDown: (event: React.PointerEvent) => void;
  onPointerMove: (event: React.PointerEvent) => void;
  onPointerUp: (event: React.PointerEvent) => void;
  reset: () => void;
  zoomBy: (factor: number) => void;
  panning: boolean;
  /** Viewport point → the SVG's user space, so a dragged node lands under the cursor. */
  toUser: (clientX: number, clientY: number, rect: DOMRect) => { x: number; y: number };
};

/**
 * Wheel-zoom + drag-pan over a square SVG canvas, expressed as a viewBox.
 *
 * `zoomed` is exposed so the caller can leave click handlers alone while the
 * user is only panning — without it, a drag would fire a click on release.
 */
export function usePanZoom(size: number, enabled = true): PanZoom {
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const drag = useRef<{ x: number; y: number; ox: number; oy: number } | null>(null);
  const [panning, setPanning] = useState(false);

  const clampOffset = useCallback(
    (value: number, currentZoom: number) => {
      const limit = (size * (currentZoom - 1)) / (2 * currentZoom);
      return Math.max(-limit, Math.min(limit, value));
    },
    [size]
  );

  const zoomBy = useCallback(
    (factor: number) => {
      setZoom((prev) => {
        const next = Math.max(1, Math.min(6, prev * factor));
        setOffset((o) => ({ x: clampOffset(o.x, next), y: clampOffset(o.y, next) }));
        return next;
      });
    },
    [clampOffset]
  );

  const onWheel = useCallback(
    (event: React.WheelEvent) => {
      if (!enabled) return;
      event.preventDefault();
      zoomBy(event.deltaY < 0 ? 1.12 : 1 / 1.12);
    },
    [enabled, zoomBy]
  );

  const onPointerDown = useCallback(
    (event: React.PointerEvent) => {
      if (!enabled || zoom <= 1) return;
      (event.target as Element).setPointerCapture?.(event.pointerId);
      drag.current = { x: event.clientX, y: event.clientY, ox: offset.x, oy: offset.y };
      setPanning(true);
    },
    [enabled, offset.x, offset.y, zoom]
  );

  const onPointerMove = useCallback(
    (event: React.PointerEvent) => {
      const state = drag.current;
      if (!state) return;
      // one rendered pixel is span/width user units, so the content tracks the cursor
      const svg = event.currentTarget as SVGSVGElement;
      const rect = svg.getBoundingClientRect();
      const unitsPerPixel = size / zoom / (rect.width || size);
      setOffset({
        x: clampOffset(state.ox - (event.clientX - state.x) * unitsPerPixel, zoom),
        y: clampOffset(state.oy - (event.clientY - state.y) * unitsPerPixel, zoom),
      });
    },
    [clampOffset, size, zoom]
  );

  const onPointerUp = useCallback(() => {
    drag.current = null;
    setPanning(false);
  }, []);

  const reset = useCallback(() => {
    setZoom(1);
    setOffset({ x: 0, y: 0 });
  }, []);

  const span = size / zoom;
  const x = size / 2 - span / 2 + offset.x;
  const y = size / 2 - span / 2 + offset.y;

  const toUser = useCallback(
    (clientX: number, clientY: number, rect: DOMRect) => ({
      x: x + ((clientX - rect.left) / (rect.width || size)) * span,
      y: y + ((clientY - rect.top) / (rect.height || size)) * span,
    }),
    [size, span, x, y]
  );

  return {
    viewBox: `${x} ${y} ${span} ${span}`,
    zoom,
    onWheel,
    onPointerDown,
    onPointerMove,
    onPointerUp,
    reset,
    zoomBy,
    panning,
    toUser,
  };
}

/** Shared control strip: zoom out / in / reset, in the site's mono voice. */
export function ZoomControls({ panZoom }: { panZoom: PanZoom }) {
  const button =
    "border border-line-dim px-2 py-1 font-mono text-[10px] uppercase tracking-[0.18em] text-text-dim transition-colors hover:border-line-hi hover:text-text-ghost disabled:opacity-30";
  return (
    <div className="flex items-center gap-2">
      <button type="button" className={button} onClick={() => panZoom.zoomBy(1 / 1.4)} disabled={panZoom.zoom <= 1} aria-label="Zoom out">
        −
      </button>
      <span className="w-[46px] text-center font-mono text-[10px] tabular-nums text-text-faint">
        {panZoom.zoom.toFixed(1)}×
      </span>
      <button type="button" className={button} onClick={() => panZoom.zoomBy(1.4)} disabled={panZoom.zoom >= 6} aria-label="Zoom in">
        +
      </button>
      <button type="button" className={button} onClick={panZoom.reset} disabled={panZoom.zoom <= 1} aria-label="Reset zoom">
        reset
      </button>
    </div>
  );
}

/* --------------------------------------------------------------------------
   Small shared bits
-------------------------------------------------------------------------- */
export const percent = (part: number, whole: number) =>
  whole > 0 ? `${((part / whole) * 100).toFixed(part / whole < 0.1 ? 1 : 0)}%` : "0%";

/** "3 months", "12 days", "2 years" — for the timeline gaps. */
export function humanDuration(days: number): string {
  const d = Math.abs(Math.round(days));
  if (d === 0) return "same day";
  if (d === 1) return "1 day";
  if (d < 45) return `${d} days`;
  const months = Math.round(d / 30.44);
  if (months < 18) return `${months} month${months === 1 ? "" : "s"}`;
  const years = (d / 365.25).toFixed(1).replace(/\.0$/, "");
  return `${years} years`;
}

/** "took effect 2 years ago" / "takes effect in 9 months" — for milestone dates. */
export function humanRelative(iso: string, now: number = Date.now()): string {
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return "";
  const days = (t - now) / 86_400_000;
  return days <= 0
    ? `took effect ${humanDuration(days)} ago`
    : `takes effect in ${humanDuration(days)}`;
}
