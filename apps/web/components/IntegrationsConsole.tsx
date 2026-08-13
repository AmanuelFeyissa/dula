"use client";

import { useEffect, useState } from "react";

interface Capability {
  name: string;
  side_effect: string;
  permission: string;
  requires_egress: boolean;
}

interface Plugin {
  id: string;
  version: string;
  description: string;
  state: string;
  capabilities: Capability[];
}

interface InvokeResult {
  ok: boolean;
  output: unknown;
  error: string | null;
  untrusted: boolean;
}

const preStyle = {
  background: "#0b0b0b",
  color: "#e6e6e6",
  padding: "0.75rem",
  borderRadius: 8,
  whiteSpace: "pre-wrap" as const,
  fontSize: "0.8rem",
};

export function IntegrationsConsole() {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [capability, setCapability] = useState("siem.search");
  const [argsText, setArgsText] = useState('{ "query": "HOST-7" }');
  const [result, setResult] = useState<InvokeResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function load(): Promise<void> {
    try {
      const res = await fetch("/api/plugins");
      if (!res.ok) throw new Error(`list failed (${res.status})`);
      setPlugins((await res.json()) as Plugin[]);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  useEffect(() => {
    void load();
  }, []);

  // Read-only capabilities are directly invokable; consequential ones run through an agent.
  const readCaps = plugins
    .flatMap((p) => p.capabilities)
    .filter((c) => c.side_effect === "read");

  async function invoke(e: React.FormEvent): Promise<void> {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setResult(null);
    let args: unknown;
    try {
      args = JSON.parse(argsText);
    } catch {
      setError("args must be valid JSON");
      setBusy(false);
      return;
    }
    try {
      const res = await fetch(`/api/connectors/${encodeURIComponent(capability)}/invoke`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ args }),
      });
      const data = (await res.json()) as InvokeResult & { detail?: string };
      if (!res.ok) throw new Error(data.detail ?? `invoke failed (${res.status})`);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main>
      <h1>Integrations</h1>
      <p>Signed, sandboxed connectors to external security systems (Phase 07).</p>

      <h2>Installed plugins</h2>
      <ul>
        {plugins.map((p) => (
          <li key={p.id} style={{ marginBottom: "0.5rem" }}>
            <strong>{p.id}</strong> <code>v{p.version}</code>{" "}
            <span style={{ color: p.state === "enabled" ? "#137333" : "#a15c00" }}>[{p.state}]</span>
            <ul>
              {p.capabilities.map((c) => (
                <li key={c.name}>
                  <code>{c.name}</code> — {c.side_effect}
                  {c.requires_egress ? " · needs egress" : ""}
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ul>

      <h2>Invoke a read connector</h2>
      <form onSubmit={invoke} style={{ display: "grid", gap: "0.5rem", maxWidth: 560 }}>
        <select value={capability} onChange={(e) => setCapability(e.target.value)}>
          {readCaps.map((c) => (
            <option key={c.name} value={c.name}>
              {c.name}
            </option>
          ))}
        </select>
        <textarea
          value={argsText}
          onChange={(e) => setArgsText(e.target.value)}
          rows={3}
          style={{ padding: "0.5rem", fontFamily: "monospace" }}
        />
        <button type="submit" disabled={busy} style={{ width: "fit-content" }}>
          {busy ? "Invoking…" : "Invoke"}
        </button>
      </form>

      {error ? <p style={{ color: "#b00020" }}>{error}</p> : null}
      {result ? (
        <>
          <h3>Result {result.ok ? "" : "(failed)"}</h3>
          <pre style={preStyle}>
            {result.ok ? JSON.stringify(result.output, null, 2) : result.error}
          </pre>
        </>
      ) : null}
    </main>
  );
}
