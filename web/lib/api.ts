/**
 * Typed REST client for the server's `/api/*` passthrough.
 *
 * The agent (AG-UI) is the reasoning layer; this is the deterministic browsing
 * layer — same tool dispatcher on the server, no model call, so the Explorer
 * renders instantly.
 */

import { API_BASE } from "./agui";

export type Meta = {
  citation: string;
  source: string;
  counts: { recitals: number; articles: number; annexes: number };
  tools: string[];
};

export type ProvisionResult = {
  ref: string;
  title?: string;
  text: string;
  /** The server's Markdown rendering of `text`; falls back to `text` if absent. */
  markdown?: string;
};

export type SearchHit = {
  ref: string;
  title: string;
  matches: number;
  excerpt: string;
};

export type SearchResult = {
  ref: string;
  result_count: number;
  items: SearchHit[];
  text: string;
};

export type ListResult<T = unknown> = {
  ref: string;
  count?: number;
  items: T[];
  text: string;
};

export type RiskTier = {
  tier: string;
  label: string;
  summary: string;
  legal_basis: string;
  applies_from: string;
  penalty?: string;
  annex_iii_areas?: { area: number; name: string; description: string; ref: string }[];
  practices?: { name: string; description: string; ref: string; exceptions?: string }[];
  obligations?: { obligation: string; ref: string }[];
};

export type ActorInfo = {
  actor: string;
  definition: string;
  definition_ref: string;
  key_obligations: { obligation: string; ref: string }[];
};

export type ChecklistItem = {
  title: string;
  description: string;
  action: string;
  ref: string;
};

export type AnnexArea = { area: number; name: string; ref: string };

/**
 * The heuristic screen. One type, matching what `/api/classify` actually sends —
 * a second copy under another name is how this drifted into reading a field that
 * does not exist (`matched_annex_iii_areas`), which crashed the view.
 */
export type Classification = {
  ref: string;
  verdict: string;
  likely_high_risk: boolean;
  /** Annex III areas the heuristic matched. Empty, not absent, when nothing did. */
  areas: AnnexArea[];
  disclaimer: string;
};

/**
 * Is the API base an absolute URL (local dev, or an API on its own host) or a
 * path prefix (this app mounted under a sub-path on the site's own origin)?
 */
const ABSOLUTE_BASE = /^[a-z][a-z0-9+.-]*:\/\//i.test(API_BASE);

async function get<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const query = new URLSearchParams();
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== "") query.set(key, String(value));
    }
  }
  const search = query.toString();

  // A path prefix must stay relative so the browser resolves it against whatever
  // origin serves the page — `new URL("/tools/x/api", undefined)` would throw.
  let url: string;
  if (ABSOLUTE_BASE) {
    const parsed = new URL(API_BASE + path);
    if (search) parsed.search = search;
    url = parsed.toString();
  } else {
    url = `${API_BASE}${path}${search ? `?${search}` : ""}`;
  }

  const resp = await fetch(url, { headers: { Accept: "application/json" } });
  if (!resp.ok) {
    let detail = `${resp.status} ${resp.statusText}`;
    try {
      const body = await resp.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      /* keep the status line */
    }
    throw new Error(detail);
  }
  return (await resp.json()) as T;
}

async function send<T>(method: "POST" | "PUT", path: string, body: unknown): Promise<T> {
  const resp = await fetch(API_BASE + path, {
    method,
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    let detail = `${resp.status} ${resp.statusText}`;
    try {
      const parsed = await resp.json();
      if (parsed?.detail) detail = String(parsed.detail);
    } catch {
      /* keep the status line */
    }
    throw new Error(detail);
  }
  return (await resp.json()) as T;
}

const post = <T,>(path: string, body: unknown) => send<T>("POST", path, body);
const put = <T,>(path: string, body: unknown) => send<T>("PUT", path, body);

export type Health = {
  status: string;
  provider: { base_url: string; model: string; available: boolean };
  vector_store: { status: string; document_count?: string | number; error?: string };
  tools: string[];
};

/* -- navigation, guides, diagrams, statistics ------------------------------ */

export type ArticleRef = { number: string; title: string };
export type TocSection = { number: number; title: string; articles: ArticleRef[] };
export type TocChapter = {
  number: string;
  title: string;
  label?: string;
  articles: ArticleRef[];
  sections: TocSection[];
};
export type Structure = { ref: string; chapters: TocChapter[]; text?: string };
export type Location = {
  ref: string;
  chapter: string;
  chapter_title: string;
  section: number | null;
  section_title: string | null;
  breadcrumb: string[];
  text: string;
};

export type Stats = {
  ref: string;
  corpus: {
    recitals: number; articles: number; annexes: number; chapters: number;
    sections: number; words: number; recital_words: number;
  };
  chapters: { number: string; title: string; articles: number; sections: number; words: number }[];
  longest_articles: { ref: string; title: string; words: number }[];
  shortest_articles: { ref: string; title: string; words: number }[];
  obligations: { total: number; by_actor: Record<string, number>; by_tier: Record<string, number> };
  citations: { edges: number; most_cited: { ref: string; citations: number }[] };
};

export type ProcedureStep = { n: number; title: string; detail: string; ref: string };
export type Procedure = {
  id: string; title: string; actor: string; tier: string; ref: string;
  summary: string; steps: ProcedureStep[];
};
export type ProcedureSummary = Omit<Procedure, "steps"> & { steps: number };

export type ScenarioItem = { title: string; detail: string; ref: string };
export type Scenario = {
  id: string; title: string; sector: string; summary: string; tier: string;
  refs: string[]; roles: { role: string; who: string }[];
  analysis: ScenarioItem[]; watchouts: string[]; disclaimer?: string;
};
export type ScenarioSummary = {
  id: string; title: string; sector: string; tier: string; refs: string[];
  summary: string;
};

export type RiskQuestion = {
  id: string; question: string; detail?: string; ref: string; yes: string; no: string;
};
export type RiskOutcome = {
  label: string; ref: string; summary: string; applies_from: string;
  penalty: string; actions: string[];
};
export type RiskPath = {
  title: string; ref: string; start: string;
  questions: RiskQuestion[]; outcomes: Record<string, RiskOutcome>;
};
export type ClassifyStep = { question: string; ref: string; answer: "yes" | "no" };
export type ClassifyWalk = {
  outcome: string | null; label?: string; detail?: RiskOutcome;
  question?: RiskQuestion; trace: ClassifyStep[]; complete: boolean; error?: string;
};

export type MindmapNode = {
  id?: string;
  title?: string;
  summary?: string;
  label?: string;
  ref: string;
  note?: string;
  children?: MindmapNode[];
};
export type MindmapTopic = { id: string; title: string; ref: string; summary: string };

export type GraphData = {
  nodes: string[];
  edges: Record<string, Record<string, number>>;
  most_cited: { ref: string; citations: number }[];
  edge_count: number;
};
export type GraphArticle = {
  ref: string;
  cites: { ref: string; count: number }[];
  cited_by: { ref: string; count: number }[];
};

/* -- provider settings (self-hosted deployments) --------------------------- */

export type ProviderConfig = {
  base_url: string;
  chat_model: string;
  embed_model: string;
  timeout: number;
  /** The key itself never reaches the browser; only whether one is set. */
  api_key_set: boolean;
};

export type ProviderSettings = {
  config: ProviderConfig;
  effective: { base_url: string; chat_model: string; timeout: number };
  /** Env vars that override the saved file, e.g. { base_url: "EU_AI_ACT_BASE_URL" }. */
  env_overrides: Record<string, string>;
  config_path: string;
};

export type ProviderTest = {
  reachable: boolean;
  url: string;
  models?: string[];
  error?: string;
};

export type ProviderUpdate = {
  base_url?: string;
  chat_model?: string;
  embed_model?: string;
  timeout?: number;
  api_key?: string;
  clear_api_key?: boolean;
};

export const api = {
  health: () => get<Health>("/health"),
  meta: () => get<Meta>("/api/meta"),
  articles: () => get<{ items: { number: string; title: string }[] }>("/api/articles"),
  recitals: () => get<{ items: { number: number; title: string }[] }>("/api/recitals"),
  annexes: () => get<{ items: { number: string; title: string }[] }>("/api/annexes"),
  search: (q: string, scope = "all", limit = 20) =>
    get<SearchResult>("/api/search", { q, scope, limit }),
  article: (n: string) => get<ProvisionResult>(`/api/article/${encodeURIComponent(n)}`),
  recital: (n: number) => get<ProvisionResult>(`/api/recital/${n}`),
  annex: (n: string) => get<ProvisionResult>(`/api/annex/${encodeURIComponent(n)}`),
  tiers: () => get<{ items: RiskTier[] }>("/api/tiers"),
  tier: (t: string) => get<RiskTier>(`/api/tiers/${t}`),
  actors: () => get<{ items: ActorInfo[] }>("/api/actors"),
  actor: (a: string) => get<ActorInfo>(`/api/actors/${a}`),
  checklist: (actor: string, tier?: string) =>
    get<ListResult<ChecklistItem>>(`/api/checklist/${actor}`, { tier }),
  classify: (description: string) =>
    get<Classification>("/api/classify", { description }),
  timeline: () =>
    get<ListResult<{ date: string; event: string; ref: string }>>("/api/timeline"),
  penalties: () =>
    get<ListResult<{ violation: string; fine?: string; note?: string; ref: string }>>(
      "/api/penalties"
    ),
  definitions: () =>
    get<ListResult<{ term: string; definition: string; ref: string }>>("/api/definitions"),
  governance: () =>
    get<ListResult<{ body: string; role: string; ref: string }>>("/api/governance"),
  crossrefs: () =>
    get<ListResult<{ topic: string; summary: string; ref: string; key_articles: { subject: string; ref: string }[] }>>(
      "/api/crossrefs"
    ),

  /* -- navigation -- */
  structure: () => get<Structure>("/api/structure"),
  location: (article: string) => get<Location>(`/api/structure/${encodeURIComponent(article)}`),

  /* -- guides -- */
  procedures: () => get<ListResult<ProcedureSummary>>("/api/procedures"),
  procedure: (id: string) => get<Procedure>(`/api/procedures/${encodeURIComponent(id)}`),
  scenarios: () => get<ListResult<ScenarioSummary>>("/api/scenarios"),
  scenario: (id: string) => get<Scenario>(`/api/scenarios/${encodeURIComponent(id)}`),
  riskPath: () => get<RiskPath>("/api/risk-path"),
  classifyWalk: (answers: Record<string, boolean>) =>
    post<ClassifyWalk>("/api/risk-path/classify", { answers }),

  /* -- diagrams and statistics -- */
  stats: () => get<Stats>("/api/stats"),
  graph: () => get<GraphData>("/api/graph"),
  graphArticle: (article: string) => get<GraphArticle>(`/api/graph/${encodeURIComponent(article)}`),
  governanceStructure: () =>
    get<{ title: string; ref: string; note?: string; root: GovernanceNode }>("/api/governance/structure"),
  mindmaps: () => get<{ items: MindmapTopic[] }>("/api/mindmaps"),
  mindmap: (topic: string) => get<MindmapNode>(`/api/mindmaps/${encodeURIComponent(topic)}`),
  chapterMindmap: (chapter: string) =>
    get<MindmapNode>(`/api/mindmaps/chapter/${encodeURIComponent(chapter)}`),

  /* -- provider settings -- */
  providerSettings: () => get<ProviderSettings>("/api/settings/provider"),
  saveProviderSettings: (body: ProviderUpdate) =>
    put<ProviderSettings>("/api/settings/provider", body),
  testProvider: (body: { base_url?: string; api_key?: string; timeout?: number }) =>
    post<ProviderTest>("/api/settings/provider/test", body),
};

export type GovernanceNode = {
  name: string; ref: string; note?: string; advisory?: boolean;
  children?: GovernanceNode[];
};

export const TIER_KEYS = ["prohibited", "high_risk", "limited_risk", "minimal_risk"] as const;
export const ACTOR_KEYS = [
  "provider",
  "deployer",
  "importer",
  "distributor",
  "authorised_representative",
  "operator",
] as const;

/**
 * "high_risk" → "High Risk". Display-only, and deliberately total: a field the
 * server happens to omit must not blank out a whole view.
 */
export const humanise = (key: string | null | undefined) =>
  (key ?? "").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

/**
 * Tier keys are acronyms in one case and plain words in the rest, so the generic
 * title-caser renders "gpai_systemic" as "Gpai Systemic". These are the labels the
 * Act's own vocabulary uses.
 */
export const TIER_LABEL: Record<string, string> = {
  prohibited: "Prohibited",
  high_risk: "High risk",
  limited_risk: "Limited risk",
  minimal_risk: "Minimal risk",
  gpai: "GPAI",
  gpai_systemic: "GPAI · systemic",
};

/** Like humanise, but right for tier keys; falls back for anything unrecognised. */
export const tierLabel = (key: string | null | undefined) =>
  key ? TIER_LABEL[key] ?? humanise(key) : "";
