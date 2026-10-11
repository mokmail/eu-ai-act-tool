"use client";

/**
 * The AG-UI stream inspector — the raw protocol, verbatim.
 *
 * Every event the SDK received, in order: lifecycle, text deltas, tool calls,
 * state patches. It is what the protocol looks like on the wire.
 */

import { useEffect, useRef } from "react";
import type { BaseEvent } from "@ag-ui/core";
import { Label } from "@/components/shell";

export function StreamInspector({
  events,
  endpoint,
  open,
  onClose,
}: {
  events: BaseEvent[];
  endpoint: string;
  open: boolean;
  onClose: () => void;
}) {
  const scroller = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const el = scroller.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [events.length]);

  return (
    <aside
      className={`fixed right-0 top-14 z-20 flex h-[calc(100vh-3.5rem)] w-full max-w-[420px] flex-col border-l border-line-dim bg-bg-panel transition-transform duration-300 ${
        open ? "translate-x-0" : "translate-x-full"
      }`}
      aria-hidden={!open}
    >
      <div className="flex items-center justify-between border-b border-line-dim px-5 py-4">
        <div className="flex flex-col gap-1">
          <Label>ag-ui stream</Label>
          <span className="font-mono text-[10px] text-text-faint">{endpoint}</span>
        </div>
        <button
          onClick={onClose}
          className="font-mono text-[10px] uppercase tracking-[0.28em] text-text-dim transition-colors hover:text-text-ghost"
        >
          close
        </button>
      </div>

      <div ref={scroller} className="flex-1 overflow-y-auto px-5 py-4">
        {events.length === 0 ? (
          <p className="font-display text-[12px] leading-relaxed text-text-faint">
            No events yet. Ask a question and every event the server emits will appear
            here as it arrives.
          </p>
        ) : (
          <ol className="flex flex-col gap-3">
            {events.map((event, index) => (
              <li key={index} className="flex flex-col gap-1 border-b border-line-dim pb-3">
                <div className="flex items-baseline gap-2">
                  <span className="font-mono text-[10px] tabular-nums text-text-faint">
                    {String(index + 1).padStart(3, "0")}
                  </span>
                  <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-text-ghost">
                    {event.type}
                  </span>
                </div>
                <pre className="max-h-48 overflow-auto bg-bg-void px-2 py-2 font-mono text-[10px] leading-relaxed text-text-dim">
                  {JSON.stringify(event, null, 2)}
                </pre>
              </li>
            ))}
          </ol>
        )}
      </div>
    </aside>
  );
}
