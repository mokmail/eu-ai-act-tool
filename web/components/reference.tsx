"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Badge, ErrorNote, Label, Panel, Spinner, ViewHeader } from "@/components/shell";

type Section = "tiers" | "timeline" | "penalties" | "definitions" | "governance" | "crossrefs";

const SECTIONS: { key: Section; label: string }[] = [
  { key: "tiers", label: "risk tiers" },
  { key: "timeline", label: "timeline" },
  { key: "penalties", label: "penalties" },
  { key: "definitions", label: "definitions" },
  { key: "governance", label: "governance" },
  { key: "crossrefs", label: "cross-references" },
];

export function ReferenceView({ onAsk }: { onAsk: (text: string) => void }) {
  const [section, setSection] = useState<Section>("tiers");

  const tiers = useApi(api.tiers);
  const timeline = useApi(api.timeline);
  const penalties = useApi(api.penalties);
  const definitions = useApi(api.definitions);
  const governance = useApi(api.governance);
  const crossrefs = useApi(api.crossrefs);

  const active =
    section === "tiers"
      ? tiers
      : section === "timeline"
        ? timeline
        : section === "penalties"
          ? penalties
          : section === "definitions"
            ? definitions
            : section === "governance"
              ? governance
              : crossrefs;

  const loads: Record<Section, () => void> = {
    tiers: tiers.run,
    timeline: timeline.run,
    penalties: penalties.run,
    definitions: definitions.run,
    governance: governance.run,
    crossrefs: crossrefs.run,
  };

  useEffect(() => {
    if (!active.data && !active.loading) loads[section]();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [section]);

  return (
    <div className="h-full overflow-y-auto px-5 py-8 md:px-8">
      <div className="mx-auto flex max-w-[86ch] flex-col gap-8">
        <ViewHeader
          eyebrow="reference"
          title="The framework on one page"
          lede="The curated analytical layer: risk tiers, phased application, the penalty schedule, statutory definitions, the governance bodies, and how the chapters interlock."
        />

        <div className="flex flex-wrap gap-x-5 gap-y-2">
          {SECTIONS.map((item) => (
            <button
              key={item.key}
              onClick={() => setSection(item.key)}
              className={`font-mono text-[10px] uppercase tracking-[0.28em] transition-colors ${
                section === item.key
                  ? "text-text-ghost"
                  : "text-text-dim hover:text-text-ghost"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>

        {active.loading ? <Spinner label="loading" /> : null}
        {active.error ? <ErrorNote message={active.error} /> : null}

        {/* ---- risk tiers ---- */}
        {section === "tiers" && tiers.data ? (
          <div className="rise flex flex-col divide-y divide-line-dim border-y border-line-dim">
            {tiers.data.items.map((tier) => (
              <div key={tier.tier} className="flex flex-col gap-4 py-6">
                <div className="flex flex-wrap items-baseline gap-3">
                  <h3 className="font-display text-[1.35rem] font-light tracking-[-0.02em] text-text-ghost">
                    {tier.label}
                  </h3>
                  <Badge tone="outline">{tier.applies_from}</Badge>
                  <span className="ml-auto font-mono text-[10px] text-text-faint">
                    {tier.legal_basis}
                  </span>
                </div>
                <p className="max-w-[74ch] font-display text-[14px] leading-relaxed text-text-dim">
                  {tier.summary}
                </p>
                {tier.penalty ? (
                  <p className="font-display text-[12px] text-text-faint">{tier.penalty}</p>
                ) : null}

                {tier.annex_iii_areas?.length ? (
                  <ul className="flex flex-col gap-2">
                    {tier.annex_iii_areas.map((area) => (
                      <li key={area.area} className="flex gap-3">
                        <span className="font-mono text-[10px] tabular-nums text-text-faint">
                          {String(area.area).padStart(2, "0")}
                        </span>
                        <span className="font-display text-[13px] leading-relaxed text-text-dim">
                          <span className="text-text-ghost">{area.name}</span> — {area.description}
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : null}

                {tier.practices?.length ? (
                  <ul className="flex flex-col gap-3">
                    {tier.practices.map((practice) => (
                      <li key={practice.name} className="border-l border-line-hi pl-4">
                        <div className="flex flex-wrap items-baseline gap-3">
                          <span className="font-display text-[13px] text-text-ghost">
                            {practice.name}
                          </span>
                          <span className="font-mono text-[10px] text-text-faint">
                            {practice.ref}
                          </span>
                        </div>
                        <p className="mt-1 font-display text-[13px] leading-relaxed text-text-dim">
                          {practice.description}
                        </p>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>
            ))}
          </div>
        ) : null}

        {/* ---- timeline ---- */}
        {section === "timeline" && timeline.data ? (
          <ul className="rise flex flex-col divide-y divide-line-dim border-y border-line-dim">
            {timeline.data.items.map((event) => (
              <li key={event.date + event.event} className="flex flex-col gap-1 py-4 md:flex-row md:gap-6">
                <span className="w-40 shrink-0 font-mono text-[11px] tabular-nums text-text-ghost">
                  {event.date}
                </span>
                <span className="font-display text-[14px] leading-relaxed text-text-dim">
                  {event.event}
                  <span className="ml-3 font-mono text-[10px] text-text-faint">{event.ref}</span>
                </span>
              </li>
            ))}
          </ul>
        ) : null}

        {/* ---- penalties ---- */}
        {section === "penalties" && penalties.data ? (
          <ul className="rise flex flex-col divide-y divide-line-dim border-y border-line-dim">
            {penalties.data.items.map((row) => (
              <li key={row.violation} className="flex flex-col gap-2 py-4">
                <div className="flex flex-wrap items-baseline gap-3">
                  <span className="font-display text-[14px] text-text-ghost">{row.violation}</span>
                  <span className="ml-auto font-mono text-[10px] text-text-faint">{row.ref}</span>
                </div>
                {row.fine ? (
                  <span className="font-mono text-[12px] text-text-dim">{row.fine}</span>
                ) : null}
                {row.note ? (
                  <span className="font-display text-[13px] leading-relaxed text-text-faint">
                    {row.note}
                  </span>
                ) : null}
              </li>
            ))}
          </ul>
        ) : null}

        {/* ---- definitions ---- */}
        {section === "definitions" && definitions.data ? (
          <dl className="rise flex flex-col divide-y divide-line-dim border-y border-line-dim">
            {definitions.data.items.map((entry) => (
              <div key={entry.term} className="flex flex-col gap-2 py-4">
                <dt className="flex items-baseline gap-3">
                  <span className="font-display text-[14px] text-text-ghost">
                    {entry.term.replace(/_/g, " ")}
                  </span>
                  <span className="font-mono text-[10px] text-text-faint">{entry.ref}</span>
                </dt>
                <dd className="max-w-[74ch] font-display text-[13px] leading-relaxed text-text-dim">
                  {entry.definition}
                </dd>
              </div>
            ))}
          </dl>
        ) : null}

        {/* ---- governance ---- */}
        {section === "governance" && governance.data ? (
          <ul className="rise flex flex-col divide-y divide-line-dim border-y border-line-dim">
            {governance.data.items.map((body) => (
              <li key={body.body} className="flex flex-col gap-2 py-4">
                <div className="flex flex-wrap items-baseline gap-3">
                  <span className="font-display text-[14px] text-text-ghost">{body.body}</span>
                  <span className="ml-auto font-mono text-[10px] text-text-faint">{body.ref}</span>
                </div>
                <p className="max-w-[74ch] font-display text-[13px] leading-relaxed text-text-dim">
                  {body.role}
                </p>
              </li>
            ))}
          </ul>
        ) : null}

        {/* ---- cross references ---- */}
        {section === "crossrefs" && crossrefs.data ? (
          <div className="rise flex flex-col gap-5">
            {crossrefs.data.items.map((group) => (
              <Panel key={group.topic} className="flex flex-col gap-3 px-5 py-5">
                <div className="flex flex-wrap items-baseline gap-3">
                  <Label>{group.topic.replace(/_/g, " ")}</Label>
                  <span className="ml-auto font-mono text-[10px] text-text-faint">{group.ref}</span>
                </div>
                <p className="max-w-[74ch] font-display text-[14px] leading-relaxed text-text-dim">
                  {group.summary}
                </p>
                <ul className="flex flex-wrap gap-2">
                  {(group.key_articles ?? []).map((article) => (
                    <li key={article.ref}>
                      <Badge tone="outline">
                        {article.subject} · {article.ref}
                      </Badge>
                    </li>
                  ))}
                </ul>
              </Panel>
            ))}
          </div>
        ) : null}

        <button
          onClick={() =>
            onAsk(
              `Using the Act's own structure, explain the ${SECTIONS.find(
                (s) => s.key === section
              )?.label} and what it means in practice, citing the relevant articles.`
            )
          }
          className="self-start border border-line-hi px-4 py-2 font-mono text-[10px] uppercase tracking-[0.24em] text-text-ghost transition-opacity hover:opacity-60"
        >
          ask the agent about this →
        </button>
      </div>
    </div>
  );
}
