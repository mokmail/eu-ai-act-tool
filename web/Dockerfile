# Web image: Next.js 15 production server.
#
# NEXT_PUBLIC_* values are baked into the client bundle at build time, and the
# ARG must be declared before the build stage uses it or the value is dropped.
# Build context is the REPO ROOT:
#   docker build -f web/Dockerfile -t eu-ai-act-web .

FROM node:22-bookworm-slim AS deps
WORKDIR /app
COPY web/package.json web/package-lock.json ./
RUN npm ci

FROM node:22-bookworm-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY web ./

ARG NEXT_PUBLIC_AGENT_URL=http://localhost:8000/agent
ARG NEXT_PUBLIC_API_BASE=http://localhost:8000
# Empty base path = served at the origin root (local). Set to a prefix when the
# app is mounted inside a bigger site, e.g. /tools/eu-ai-act on kmail.at.
ARG NEXT_PUBLIC_BASE_PATH=
# The server container, so the app can proxy /api and /agent to it at build time
# (rewrites are baked in). Empty leaves the app calling NEXT_PUBLIC_API_BASE.
ARG API_UPSTREAM=
# Public deployment inside another site: drop the duplicate masthead and the
# provider settings.
ARG NEXT_PUBLIC_EMBEDDED=
ENV NEXT_PUBLIC_AGENT_URL=$NEXT_PUBLIC_AGENT_URL
ENV NEXT_PUBLIC_API_BASE=$NEXT_PUBLIC_API_BASE
ENV NEXT_PUBLIC_BASE_PATH=$NEXT_PUBLIC_BASE_PATH
ENV NEXT_PUBLIC_EMBEDDED=$NEXT_PUBLIC_EMBEDDED
ENV API_UPSTREAM=$API_UPSTREAM
RUN npm run build

FROM node:22-bookworm-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
# Re-declared here on purpose: `next start` reads next.config.ts again at runtime,
# so the base path and proxy target must be present at runtime too — not only
# while building. Without this the server serves the app at "/" while the bundle
# asks for /tools/eu-ai-act/*, and every asset 404s.
ARG NEXT_PUBLIC_BASE_PATH=
ARG API_UPSTREAM=
ARG NEXT_PUBLIC_API_BASE=
ARG NEXT_PUBLIC_AGENT_URL=
ARG NEXT_PUBLIC_EMBEDDED=
ENV NEXT_PUBLIC_BASE_PATH=$NEXT_PUBLIC_BASE_PATH
ENV API_UPSTREAM=$API_UPSTREAM
ENV NEXT_PUBLIC_API_BASE=$NEXT_PUBLIC_API_BASE
ENV NEXT_PUBLIC_AGENT_URL=$NEXT_PUBLIC_AGENT_URL
ENV NEXT_PUBLIC_EMBEDDED=$NEXT_PUBLIC_EMBEDDED
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/next.config.ts ./next.config.ts
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["npm", "run", "start"]
