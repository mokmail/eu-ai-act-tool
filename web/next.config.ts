import path from "node:path";
import type { NextConfig } from "next";

/**
 * Where this app is mounted.
 *
 * Empty for local dev (served at the origin root). Set to a path prefix when the
 * app is deployed *inside* a bigger site — e.g. `/tools/eu-ai-act` on kmail.at.
 * Without it, the tool's routes and `/_next/*` assets collide with the host
 * site's own, and its `/api` would shadow the host's.
 */
const BASE_PATH = (process.env.NEXT_PUBLIC_BASE_PATH ?? "").replace(/\/+$/, "");

/**
 * The server container, for the same-origin proxy below. Empty leaves the app
 * calling whatever NEXT_PUBLIC_API_BASE points at (dev, or a separate API host).
 */
const API_UPSTREAM = (process.env.API_UPSTREAM ?? "").replace(/\/+$/, "");

const nextConfig: NextConfig = {
  // A stray lockfile above the project makes Next infer the wrong workspace root,
  // which breaks the build-trace step. Pin it to this directory.
  outputFileTracingRoot: path.join(__dirname),

  // `next dev` and `next build` share a build directory, so building while dev is
  // running corrupts the dev server's bundle: the page still returns 200, but
  // hydration dies and nothing renders. verify.sh therefore builds into its own
  // directory, leaving a running dev server untouched.
  distDir: process.env.NEXT_DIST_DIR ?? ".next",

  basePath: BASE_PATH || undefined,

  // Server-side base URL for the AG-UI backend (Docker sets this to the service name).
  env: {
    NEXT_PUBLIC_AGENT_URL:
      process.env.NEXT_PUBLIC_AGENT_URL ?? "http://127.0.0.1:8000/agent",
    NEXT_PUBLIC_API_BASE:
      process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000",
  },

  async rewrites() {
    // Mounted under a path on the site's own origin, the browser and the API
    // share an origin, so proxy both the REST passthrough and the AG-UI agent
    // stream to the server. One origin, no CORS, and only one rule to route at
    // the edge.
    if (!API_UPSTREAM) return [];
    return [
      { source: "/api/:path*", destination: `${API_UPSTREAM}/api/:path*` },
      // The header's status dot reads /health; unproxied it 404s and the app
      // sits on "connecting" forever.
      { source: "/health", destination: `${API_UPSTREAM}/health` },
      { source: "/agent", destination: `${API_UPSTREAM}/agent` },
    ];
  },
};

export default nextConfig;
