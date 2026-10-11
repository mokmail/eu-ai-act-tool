"use client";

/**
 * Settings — pointing the app at your own inference server.
 *
 * The model and provider are deliberately absent from the rest of the chrome:
 * on your own infrastructure they are an implementation detail, not a feature
 * to advertise. Everything about them lives here.
 *
 * Two things this page is careful to say out loud:
 *   * an environment variable beats the saved file, so a field that appears to
 *     do nothing is almost always being overridden — that is called out inline;
 *   * the API key is write-only. The server never sends it back, so the field
 *     starts empty and only a change is ever saved.
 */

import { useCallback, useEffect, useState } from "react";

import { api, type ProviderSettings, type ProviderTest } from "@/lib/api";
import { Label, Panel, Spinner, ViewHeader } from "@/components/shell";

const FIELD =
  "w-full border border-line-dim bg-bg-panel px-3 py-2 font-mono text-[12px] text-text-ghost outline-none transition-colors placeholder:text-text-faint focus:border-line-hi";

const BUTTON =
  "border px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] transition-colors disabled:opacity-40";

const EXAMPLES = [
  { label: "Ollama", url: "http://localhost:11434/v1" },
  { label: "vLLM / TGI", url: "http://your-gpu-host:8000/v1" },
  { label: "llama.cpp", url: "http://localhost:8080/v1" },
  { label: "OpenAI-compatible gateway", url: "https://api.example.com/v1" },
];

export function SettingsView() {
  const [current, setCurrent] = useState<ProviderSettings | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [testing, setTesting] = useState(false);
  const [test, setTest] = useState<ProviderTest | null>(null);

  const [baseUrl, setBaseUrl] = useState("");
  const [chatModel, setChatModel] = useState("");
  const [embedModel, setEmbedModel] = useState("");
  const [timeoutValue, setTimeoutValue] = useState("120");
  const [apiKey, setApiKey] = useState("");
  const [clearKey, setClearKey] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await api.providerSettings();
      setCurrent(data);
      setBaseUrl(data.config.base_url);
      setChatModel(data.config.chat_model);
      setEmbedModel(data.config.embed_model);
      setTimeoutValue(String(data.config.timeout));
      setApiKey("");
      setClearKey(false);
      setLoadError(null);
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : String(error));
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const runTest = async () => {
    setTesting(true);
    setTest(null);
    try {
      setTest(
        await api.testProvider({
          base_url: baseUrl,
          api_key: apiKey || undefined,
          timeout: Number(timeoutValue) || undefined,
        })
      );
    } catch (error) {
      setTest({
        reachable: false,
        url: baseUrl,
        error: error instanceof Error ? error.message : String(error),
      });
    } finally {
      setTesting(false);
    }
  };

  const save = async () => {
    setSaving(true);
    setSaveError(null);
    try {
      const data = await api.saveProviderSettings({
        base_url: baseUrl,
        chat_model: chatModel,
        embed_model: embedModel,
        timeout: Number(timeoutValue) || undefined,
        api_key: apiKey || undefined,
        clear_api_key: clearKey || undefined,
      });
      setCurrent(data);
      setApiKey("");
      setClearKey(false);
      setSaved(true);
      window.setTimeout(() => setSaved(false), 2600);
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : String(error));
    } finally {
      setSaving(false);
    }
  };

  if (loadError) {
    return (
      <div className="flex flex-col">
        <ViewHeader
          eyebrow="System"
          title="Settings"
          lede="Point the app at your own inference server."
        />
        <div className="pt-8">
          <Panel className="px-4 py-3">
            <Label faint>the settings endpoint did not answer</Label>
            <p className="mt-2 font-display text-[13px] leading-relaxed text-text-dim">
              {loadError}. The server may be older than this build — restart it and reload.
            </p>
          </Panel>
        </div>
      </div>
    );
  }

  if (!current) {
    return (
      <div className="flex flex-col">
        <ViewHeader eyebrow="System" title="Settings" lede="Point the app at your own inference server." />
        <div className="pt-8">
          <Spinner label="reading the provider config" />
        </div>
      </div>
    );
  }

  const overrides = current.env_overrides;
  const overridden = (field: string) => overrides[field];

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-[1500px] px-5 py-10 md:px-10">
        <ViewHeader
          eyebrow="System"
          title="Settings"
          lede="The app answers from any OpenAI-compatible endpoint — a local Ollama, a vLLM on your own GPU, or a gateway. Nothing here is sent anywhere else."
        />

        {/* Constrained: a text input stretched to 1400px is hard to read and the
            label/value pairs drift a screen apart. */}
        <div className="flex max-w-[820px] flex-col gap-10 pt-8">
        {Object.keys(overrides).length ? (
          <Panel className="border-line-hi px-4 py-3">
            <Label faint>environment variables are overriding the file</Label>
            <ul className="mt-2 flex flex-col gap-1">
              {Object.entries(overrides).map(([field, variable]) => (
                <li
                  key={field}
                  className="font-mono text-[11px] tracking-[0.06em] text-text-dim"
                >
                  {variable} sets <span className="text-text-ghost">{field.replace(/_/g, " ")}</span>
                  {" — the value below is saved but will not take effect until it is unset."}
                </li>
              ))}
            </ul>
          </Panel>
        ) : null}

        {/* connection ---------------------------------------------------- */}
        <section className="flex flex-col gap-5">
          <Label>Connection</Label>

          <label className="flex flex-col gap-2">
            <span className="flex items-baseline justify-between gap-4">
              <Label faint>base url</Label>
              {overridden("base_url") ? (
                <Label faint>overridden by {overridden("base_url")}</Label>
              ) : null}
            </span>
            <input
              className={FIELD}
              value={baseUrl}
              onChange={(event) => setBaseUrl(event.target.value)}
              placeholder="http://localhost:11434/v1"
              spellCheck={false}
              autoComplete="off"
            />
            <span className="font-display text-[12px] leading-relaxed text-text-faint">
              Must end in <code className="font-mono">/v1</code> — the OpenAI-compatible route.
            </span>
          </label>

          <div className="flex flex-wrap items-center gap-3">
            {EXAMPLES.map((example) => (
              <button
                key={example.label}
                type="button"
                onClick={() => setBaseUrl(example.url)}
                className="border border-line-dim px-2 py-1 font-mono text-[10px] uppercase tracking-[0.16em] text-text-dim transition-colors hover:border-line-hi hover:text-text-ghost"
              >
                {example.label}
              </button>
            ))}
          </div>

          <label className="flex flex-col gap-2">
            <span className="flex items-baseline justify-between gap-4">
              <Label faint>api key</Label>
              <Label faint>{current.config.api_key_set ? "one is set" : "none set"}</Label>
            </span>
            <input
              className={FIELD}
              type="password"
              value={apiKey}
              onChange={(event) => {
                setApiKey(event.target.value);
                setClearKey(false);
              }}
              placeholder={current.config.api_key_set ? "•••••••• (leave empty to keep)" : "not required for local servers"}
              spellCheck={false}
              autoComplete="off"
              disabled={clearKey}
            />
            {current.config.api_key_set ? (
              <button
                type="button"
                onClick={() => {
                  setClearKey((prev) => !prev);
                  setApiKey("");
                }}
                className={`w-fit ${BUTTON} ${
                  clearKey
                    ? "border-text-ghost text-text-ghost"
                    : "border-line-dim text-text-dim hover:border-line-hi"
                }`}
              >
                {clearKey ? "will be removed on save" : "remove the saved key"}
              </button>
            ) : null}
          </label>

          <label className="flex flex-col gap-2 sm:max-w-[220px]">
            <Label faint>timeout (seconds)</Label>
            <input
              className={FIELD}
              type="number"
              min={5}
              max={600}
              value={timeoutValue}
              onChange={(event) => setTimeoutValue(event.target.value)}
            />
          </label>

          <div className="flex flex-wrap items-center gap-4">
            <button
              type="button"
              onClick={runTest}
              disabled={testing}
              className={`${BUTTON} border-line-dim text-text-dim hover:border-line-hi hover:text-text-ghost`}
            >
              {testing ? "probing…" : "test connection"}
            </button>

            <button
              type="button"
              onClick={save}
              disabled={saving}
              className={`${BUTTON} ${
                saved
                  ? "border-text-ghost text-text-ghost"
                  : "border-line-hi text-text-ghost hover:bg-bg-panel-hi"
              }`}
            >
              {saving ? "saving…" : saved ? "saved" : "save"}
            </button>

            {saveError ? <span className="font-mono text-[11px] text-text-dim">{saveError}</span> : null}
          </div>

          {test ? (
            <Panel className="flex flex-col gap-3 px-4 py-3">
              <span className="flex items-baseline gap-3">
                <Label faint>{test.reachable ? "reachable" : "no answer"}</Label>
                <span className="font-mono text-[11px] text-text-dim">{test.url}</span>
              </span>
              {test.reachable ? (
                <span className="font-display text-[13px] leading-relaxed text-text-dim">
                  {test.models?.length ?? 0} model{(test.models?.length ?? 0) === 1 ? "" : "s"} offered
                  {chatModel && test.models?.includes(chatModel)
                    ? ` · ${chatModel} is among them`
                    : chatModel
                      ? ` · ${chatModel} was not listed — it may still work`
                      : ""}
                  .
                </span>
              ) : (
                <span className="font-display text-[13px] leading-relaxed text-text-dim">
                  {test.error}
                </span>
              )}
            </Panel>
          ) : null}
        </section>

        {/* models -------------------------------------------------------- */}
        <section className="flex flex-col gap-5 border-t border-line-dim pt-8">
          <Label>Models</Label>

          <label className="flex flex-col gap-2">
            <span className="flex items-baseline justify-between gap-4">
              <Label faint>chat model</Label>
              {overridden("chat_model") ? (
                <Label faint>overridden by {overridden("chat_model")}</Label>
              ) : null}
            </span>
            <input
              className={FIELD}
              value={chatModel}
              onChange={(event) => setChatModel(event.target.value)}
              list="provider-models"
              placeholder="the model that answers questions"
              spellCheck={false}
              autoComplete="off"
            />
            <datalist id="provider-models">
              {(test?.models ?? []).map((model) => (
                <option key={model} value={model} />
              ))}
            </datalist>
            <span className="font-display text-[12px] leading-relaxed text-text-faint">
              Needs to support tool calling — the agent reads the Act through tools, not memory.
            </span>
          </label>

          <label className="flex flex-col gap-2">
            <Label faint>embedding model</Label>
            <input
              className={FIELD}
              value={embedModel}
              onChange={(event) => setEmbedModel(event.target.value)}
              list="provider-models"
              placeholder="the model that indexes the Act for retrieval"
              spellCheck={false}
              autoComplete="off"
            />
            <span className="font-display text-[12px] leading-relaxed text-text-faint">
              Changing this invalidates the existing vector index; rebuild it from the CLI
              (<code className="font-mono">eu-ai-act index --rebuild</code>) to pick it up.
            </span>
          </label>
        </section>

        {/* storage ------------------------------------------------------- */}
        <section className="flex flex-col gap-4 border-t border-line-dim pt-8">
          <Label>Where this is kept</Label>
          <dl className="flex flex-col gap-[6px] font-mono text-[11px] text-text-dim">
            <div className="flex flex-wrap justify-between gap-4">
              <dt>config file</dt>
              <dd className="text-text-ghost">{current.config_path}</dd>
            </div>
            <div className="flex flex-wrap justify-between gap-4">
              <dt>in effect now</dt>
              <dd className="text-text-ghost">
                {current.effective.base_url} · {current.effective.chat_model}
              </dd>
            </div>
          </dl>
          <p className="max-w-[76ch] font-display text-[12px] leading-relaxed text-text-faint">
            Containerised deployments can skip this page entirely — set{" "}
            <code className="font-mono">EU_AI_ACT_BASE_URL</code>,{" "}
            <code className="font-mono">EU_AI_ACT_CHAT_MODEL</code> and{" "}
            <code className="font-mono">EU_AI_ACT_API_KEY</code> on the server and the file is
            ignored.
          </p>
        </section>

        {/* the CLI -------------------------------------------------------
            These install notes used to be the page at /tools/eu-ai-act on the
            site. The app took that path over, so they live here now — with the
            tool, where someone who wants the terminal version will look. */}
        <section className="flex flex-col gap-4 border-t border-line-dim pt-8">
          <Label>From the command line</Label>
          <p className="max-w-[76ch] font-display text-[12px] leading-relaxed text-text-dim">
            The same Act and the same citations without a browser. Ships the full dataset — 180
            recitals, 113 articles, 13 annexes — with a CLI and an interactive Textual TUI, and a
            local assistant grounded in a vector store rather than in model memory.
          </p>
          <dl className="flex flex-col gap-[6px] font-mono text-[11px] text-text-dim">
            <div className="flex flex-wrap justify-between gap-4">
              <dt>install</dt>
              <dd className="text-text-ghost">curl -fsSL https://kmail.at/run-tui.sh | sh</dd>
            </div>
            <div className="flex flex-wrap justify-between gap-4">
              <dt>usage</dt>
              <dd className="text-text-ghost">
                eu-ai-act &lt;search|article|tier|checklist|ai|…&gt; [args]
              </dd>
            </div>
            <div className="flex flex-wrap justify-between gap-4">
              <dt>source</dt>
              <dd>
                <a
                  href="https://github.com/mokmail/eu-ai-act-tool"
                  target="_blank"
                  rel="noreferrer"
                  className="text-text-ghost underline decoration-line-hi underline-offset-4 transition-colors hover:decoration-text-ghost"
                >
                  github.com/mokmail/eu-ai-act-tool
                </a>
              </dd>
            </div>
          </dl>
        </section>
        </div>
      </div>
    </div>
  );
}
