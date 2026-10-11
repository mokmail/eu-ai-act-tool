/**
 * End-to-end smoke test for the AG-UI path.
 *
 * Drives the *real* `@ag-ui/client` HttpAgent against the running server, so it
 * exercises exactly what the browser does: build RunAgentInput from the message
 * store, POST it, parse the SSE stream, validate the events, and fire the typed
 * subscriber hooks. Asserts the run lifecycle and prints the answer.
 *
 *   node scripts/smoke-agui.mjs ["your question"] [agent-url]
 */
import { HttpAgent } from "@ag-ui/client";

const question =
  process.argv[2] ?? "What AI practices are prohibited under Article 5?";
const url = process.argv[3] ?? "http://127.0.0.1:8000/agent";

const types = [];
const tools = [];
let text = "";
let sources = [];
let failed = null;

const agent = new HttpAgent({ url, threadId: "smoke-thread" });
agent.messages = [{ id: "m1", role: "user", content: question }];

agent.subscribe({
  onEvent: ({ event }) => types.push(event.type),
  onTextMessageContentEvent: ({ event }) => {
    text += event.delta;
  },
  onToolCallStartEvent: ({ event }) => {
    tools.push(event.toolCallName);
    process.stdout.write(`\n  [tool] ${event.toolCallName}`);
  },
  onToolCallResultEvent: ({ event }) => {
    const raw = typeof event.content === "string" ? event.content : "";
    let ref = "";
    try {
      ref = JSON.parse(raw).ref ?? "";
    } catch {
      /* not JSON */
    }
    process.stdout.write(` → ${ref}`);
  },
  onCustomEvent: ({ event }) => {
    if (event.name === "sources") sources = event.value ?? [];
  },
  onRunErrorEvent: ({ event }) => {
    failed = event.message;
  },
  onRunFailed: ({ error }) => {
    failed = error.message;
  },
});

console.log(`POST ${url}\nQ: ${question}\n`);
const started = Date.now();
await agent.runAgent({ runId: "smoke-run" });
const elapsed = ((Date.now() - started) / 1000).toFixed(1);

console.log(`\n\n--- ${elapsed}s ---`);
console.log("events:", types.length, "| first:", types[0], "| last:", types.at(-1));
console.log("tools :", tools.length ? tools.join(", ") : "(none)");
console.log("sources:", sources.length ? sources.join(", ") : "(none)");
console.log("\nanswer:\n" + text.slice(0, 900));

const problems = [];
if (failed) problems.push(`run failed: ${failed}`);
if (types[0] !== "RUN_STARTED") problems.push("run did not start with RUN_STARTED");
if (types.at(-1) !== "RUN_FINISHED") problems.push("run did not end with RUN_FINISHED");
if (!text.trim()) problems.push("no assistant text was streamed");
if (!tools.length) problems.push("the model made no tool call");
if (!sources.length) problems.push("no sources reported");

if (problems.length) {
  console.error("\nFAIL:\n - " + problems.join("\n - "));
  process.exit(1);
}
console.log("\nPASS: run lifecycle, tool calling, streamed text and sources all verified.");
