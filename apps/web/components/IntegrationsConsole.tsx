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

export function IntegrationsConsole() {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [capability, setCapability] = useState("siem.search");
  const [argsText, setArgsText] = useState('{ "query": "HOST-7" }');
  const [result, setResult] = useState<InvokeResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function load(): Promise<void> {
    try {
      const res = await fetch("/api/plugins");
      if (!res.ok) {
        throw new Error(
          res.status === 401
            ? "Your session expired — sign in again."
            : `Couldn't load connectors (${res.status})`,
        );
      }
      setPlugins((await res.json()) as Plugin[]);
      setLoadError(null);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : String(err));
    }
  }

  useEffect(() => {
    void load();
  }, []);

  // Read-only capabilities are directly invokable; consequential ones run through an agent.
  const readCaps = plugins.flatMap((p) => p.capabilities).filter((c) => c.side_effect === "read");

  async function invoke(e: React.FormEvent): Promise<void> {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setResult(null);
    let args: unknown;
    try {
      args = JSON.parse(argsText);
    } catch {
      setError("Arguments must be valid JSON.");
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
      if (!res.ok) throw new Error(data.detail ?? `Invoke failed (${res.status})`);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <header className="page__head">
        <h1>Integrations</h1>
        <p className="page__desc">
          Signed, sandboxed connectors to external security systems. Read-only capabilities can be
          run here; consequential ones only run through an agent, behind an approval.
        </p>
      </header>

      <h2>Installed connectors</h2>
      {loadError ? (
        <div className="notice notice--warn" style={{ marginBottom: 18 }}>
          <div className="notice__title">Couldn&apos;t load connectors</div>
          <div className="muted">{loadError}</div>
        </div>
      ) : plugins.length === 0 ? (
        <div className="panel" style={{ marginBottom: 18 }}>
          <div className="empty">
            <div className="empty__title">No connectors installed</div>
          </div>
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: 12,
            marginBottom: 24,
          }}
        >
          {plugins.map((p) => (
            <div key={p.id} className="card">
              <div className="row" style={{ justifyContent: "space-between", marginBottom: 4 }}>
                <strong className="mono" style={{ fontSize: 13.5 }}>
                  {p.id}
                </strong>
                <span className={`chip ${p.state === "enabled" ? "chip--ok" : "chip--medium"}`}>
                  {p.state}
                </span>
              </div>
              <div className="faint" style={{ fontSize: 12 }}>
                v{p.version}
              </div>
              <p className="muted" style={{ fontSize: 13, margin: "6px 0 10px" }}>
                {p.description}
              </p>
              <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                {p.capabilities.map((c) => (
                  <li key={c.name} className="row" style={{ gap: 6, marginBottom: 5 }}>
                    <code className="mono">{c.name}</code>
                    <span
                      className={`chip ${c.side_effect === "read" ? "chip--info" : "chip--medium"}`}
                      style={{ fontSize: 11 }}
                    >
                      {c.side_effect === "read" ? "Read-only" : "Consequential"}
                    </span>
                    {c.requires_egress ? (
                      <span className="chip chip--medium" style={{ fontSize: 11 }}>
                        Needs egress
                      </span>
                    ) : null}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}

      <h2>Run a read connector</h2>
      <form onSubmit={invoke} className="card" style={{ maxWidth: 620 }}>
        <label
          htmlFor="cap"
          className="faint"
          style={{ fontSize: 12, display: "block", marginBottom: 6 }}
        >
          Capability
        </label>
        <select
          id="cap"
          className="select"
          value={capability}
          onChange={(e) => setCapability(e.target.value)}
          style={{ marginBottom: 10 }}
        >
          {readCaps.length === 0 ? <option value="siem.search">siem.search</option> : null}
          {readCaps.map((c) => (
            <option key={c.name} value={c.name}>
              {c.name}
            </option>
          ))}
        </select>
        <label
          htmlFor="args"
          className="faint"
          style={{ fontSize: 12, display: "block", marginBottom: 6 }}
        >
          Arguments (JSON)
        </label>
        <textarea
          id="args"
          className="textarea"
          value={argsText}
          onChange={(e) => setArgsText(e.target.value)}
          rows={3}
        />
        <button
          type="submit"
          className="btn btn--primary"
          disabled={busy}
          style={{ marginTop: 12 }}
        >
          {busy ? "Running…" : "Run connector"}
        </button>
      </form>

      {error ? (
        <div className="notice notice--danger" style={{ marginTop: 18 }}>
          <div className="notice__title">That didn&apos;t work</div>
          <div className="muted">{error}</div>
        </div>
      ) : null}

      {result ? (
        <section style={{ marginTop: 18 }}>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <h3 style={{ margin: 0 }}>Result</h3>
            <span className="row" style={{ gap: 8 }}>
              <span className={`chip ${result.ok ? "chip--ok" : "chip--critical"}`}>
                {result.ok ? "Success" : "Failed"}
              </span>
              {result.untrusted ? <span className="chip chip--info">Untrusted output</span> : null}
            </span>
          </div>
          <pre className="output output--code" style={{ marginTop: 8 }}>
            {result.ok ? JSON.stringify(result.output, null, 2) : result.error}
          </pre>
        </section>
      ) : null}
    </>
  );
}
