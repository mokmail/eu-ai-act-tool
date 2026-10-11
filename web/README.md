# EU AI Act — web client

Next.js 15 (App Router) · React 19 · Tailwind v4 · `@ag-ui/client`.

The client for the EU AI Act navigator. It talks to the FastAPI AG-UI server in
[`../server`](../server) — **start that first**, or nothing will answer.

## Run

```bash
npm install
npm run dev
```

Serves on http://localhost:3000 (or the next free port). The server is expected at
`http://127.0.0.1:8000`; point elsewhere with:

```bash
NEXT_PUBLIC_AGENT_URL=http://host:8000/agent \
NEXT_PUBLIC_API_BASE=http://host:8000 \
npm run dev
```

Both are build-time values, so they must be set before `npm run build` for a
production bundle (see `next.config.ts` and `web/Dockerfile`).

## Embedded ("public") build

`NEXT_PUBLIC_EMBEDDED=1` marks a deployment hosted inside another site — kmail.at
renders its own page and embeds this app at `/tools/eu-ai-act/app`. The host page
carries the masthead and the footer, so this app drops both, and the provider
**Settings** view goes with them (its nav group is absent and `page.tsx` refuses
the view even if requested directly).

The layout adapts so nothing is stranded:

- At `lg` and up the header strip (`SiteHeader`) is `hidden` and the sidebar is
  permanent — `navOpen` is forced expanded, because the collapse toggle lives in
  that strip and a collapsed rail would be a dead end. The main pane takes the
  full viewport height (`lg:h-screen`).
- Below `lg` the header returns: there the sidebar is an overlay drawer and the
  header is the only way to open it, so `main` subtracts its height.

Standalone builds keep the header at every width, let the sidebar collapse to a
rail of section numbers, and leave Settings in place.

## Layout

```
app/            App Router: layout (fonts + theme), page (shell), globals.css (design tokens)
components/     ask · map · mindmap · charts · reference · classify · guides · tools · stream · shell
  diagrams.tsx  SVG primitives: organigram, radial mindmap, step flow, bar chart, timeline, citation graph
lib/            agui.ts (HttpAgent hook) · api.ts (REST client) · useApi.ts
scripts/        smoke-agui.mjs — end-to-end test against a running server
```

`lib/agui.ts` is the only place that touches the AG-UI protocol: it wraps
`HttpAgent`, subscribes to the SDK's typed event hooks, and folds them into the
transcript the UI renders (text deltas, tool-call cards, run lifecycle, sources).

## Gotcha: `next dev` and `next build` share `.next`

Never run `npm run build` while `npm run dev` is running in the same directory.
Both write `.next`; the build's output gets clobbered by the dev server and
`next build` reports nonsensical route sizes (`0 B`) — or fails outright. Stop
the dev server, build, then restart it.

## Verify

```bash
npm run build                          # type-check + production build
node scripts/smoke-agui.mjs            # needs the server running
```

See the [root README](../README.md) for the full picture.
