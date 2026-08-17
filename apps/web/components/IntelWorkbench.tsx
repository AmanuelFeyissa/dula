"use client";

import { useState } from "react";

interface Indicator {
  kind: string;
  value: string;
  defanged: string;
}

interface Technique {
  id: string;
  name: string;
  tactic: string;
}

interface ExtractResult {
  indicators: Indicator[];
  techniques: Technique[];
  stix_bundle: unknown;
  summary: string | null;
}

interface VulnResult {
  base_score: number;
  severity: string;
  priority: string;
  risk_score: number;
  rationale: string[];
}

interface RuleResult {
  rule: string;
  valid: boolean;
  errors: string[];
  warnings: string[];
}

type Tab = "extract" | "vuln" | "detect";

// Presentation comes from the design system (app/globals.css) so the workbench matches the
// rest of the console; only layout-specific spacing stays inline.

function stixObjectCount(bundle: unknown): number {
  if (bundle && typeof bundle === "object" && Array.isArray((bundle as { objects?: unknown }).objects)) {
    return (bundle as { objects: unknown[] }).objects.length;
  }
  return 0;
}

async function post<T>(path: string, payload: unknown): Promise<T> {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = (await res.json()) as T & { detail?: string };
  if (!res.ok) {
    throw new Error(body.detail ?? `request failed (${res.status})`);
  }
  return body;
}

function ExtractPanel() {
  const [advisory, setAdvisory] = useState("");
  const [result, setResult] = useState<ExtractResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function run(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      setResult(await post<ExtractResult>("/api/intel/extract", { advisory, summarize: true }));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <p>
        Paste an advisory to extract defanged IOCs and ATT&CK techniques, with a grounded
        summary and a STIX 2.1 bundle.
      </p>
      <form onSubmit={run}>
        <textarea
          value={advisory}
          onChange={(e) => setAdvisory(e.target.value)}
          rows={6}
          placeholder="Paste a threat advisory or incident report…"
          className="textarea"
        />
        <button type="submit" className="btn btn--primary" disabled={busy || !advisory.trim()} style={{ marginTop: 12 }}>
          {busy ? "Extracting…" : "Extract"}
        </button>
      </form>
      {error ? (
        <div className="notice notice--danger" style={{ marginTop: 12 }}>{error}</div>
      ) : null}
      {result ? (
        <>
          <h3>Indicators</h3>
          <ul>
            {result.indicators.map((i, idx) => (
              <li key={idx}>
                <code>{i.kind}</code>: {i.defanged}
              </li>
            ))}
          </ul>
          <h3>ATT&CK Techniques</h3>
          <ul>
            {result.techniques.map((t) => (
              <li key={t.id}>
                <strong>{t.id}</strong> {t.name} ({t.tactic})
              </li>
            ))}
          </ul>
          {result.summary ? (
            <>
              <h3>Summary</h3>
              <div className="output output--prose">{result.summary}</div>
            </>
          ) : null}
          <details className="disclose">
            <summary>
              <h3 style={{ display: "inline" }}>STIX 2.1 Bundle</h3>{" "}
              <span className="faint">({stixObjectCount(result.stix_bundle)} objects)</span>
            </summary>
            <div className="row" style={{ justifyContent: "flex-end", margin: "8px 0" }}>
              <button
                type="button"
                className="btn btn--ghost"
                onClick={() =>
                  void navigator.clipboard?.writeText(JSON.stringify(result.stix_bundle, null, 2))
                }
              >
                Copy JSON
              </button>
            </div>
            <pre className="output output--code">{JSON.stringify(result.stix_bundle, null, 2)}</pre>
          </details>
        </>
      ) : null}
    </>
  );
}

function VulnPanel() {
  const [vector, setVector] = useState("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H");
  const [knownExploited, setKnownExploited] = useState(false);
  const [internetFacing, setInternetFacing] = useState(false);
  const [result, setResult] = useState<VulnResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function run(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      setResult(
        await post<VulnResult>("/api/intel/vulnerability", {
          cvss_vector: vector,
          known_exploited: knownExploited,
          internet_facing: internetFacing,
        }),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <p>Score a CVSS v3.1 vector and get an explainable remediation priority.</p>
      <form onSubmit={run} className="card stack" style={{ maxWidth: 520 }}>
        <input
          value={vector}
          onChange={(e) => setVector(e.target.value)}
          placeholder="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
          className="input"
        />
        <label>
          <input
            type="checkbox"
            checked={knownExploited}
            onChange={(e) => setKnownExploited(e.target.checked)}
          />{" "}
          Known-exploited (KEV)
        </label>
        <label>
          <input
            type="checkbox"
            checked={internetFacing}
            onChange={(e) => setInternetFacing(e.target.checked)}
          />{" "}
          Internet-facing asset
        </label>
        <button type="submit" className="btn btn--primary" disabled={busy}>
          {busy ? "Scoring…" : "Analyze"}
        </button>
      </form>
      {error ? (
        <div className="notice notice--danger" style={{ marginTop: 12 }}>{error}</div>
      ) : null}
      {result ? (
        <>
          <h3>
            {result.severity.toUpperCase()} ({result.base_score}) → priority {result.priority}
          </h3>
          <ul>
            {result.rationale.map((r, idx) => (
              <li key={idx}>{r}</li>
            ))}
          </ul>
        </>
      ) : null}
    </>
  );
}

function DetectPanel() {
  const [format, setFormat] = useState<"sigma" | "yara">("sigma");
  const [title, setTitle] = useState("");
  const [advisory, setAdvisory] = useState("");
  const [result, setResult] = useState<RuleResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function run(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const path = format === "sigma" ? "/api/intel/sigma" : "/api/intel/yara";
      const payload =
        format === "sigma"
          ? { title, advisory, category: "proxy", attack_tags: [] }
          : { name: title.replace(/[^A-Za-z0-9_]/g, "_") || "Detection", advisory };
      setResult(await post<RuleResult>(path, payload));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <p>Author a Sigma or YARA rule from an advisory&apos;s indicators. Always validated.</p>
      <div style={{ marginBottom: "1rem" }}>
        <label style={{ marginRight: "1rem" }}>
          <input
            type="radio"
            checked={format === "sigma"}
            onChange={() => setFormat("sigma")}
          />{" "}
          Sigma
        </label>
        <label>
          <input type="radio" checked={format === "yara"} onChange={() => setFormat("yara")} />{" "}
          YARA
        </label>
      </div>
      <form onSubmit={run} className="card stack">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder={format === "sigma" ? "Rule title" : "Rule name (identifier)"}
          className="input"
        />
        <textarea
          value={advisory}
          onChange={(e) => setAdvisory(e.target.value)}
          rows={4}
          placeholder="Advisory text containing the indicators to detect…"
          className="input"
        />
        <button type="submit" className="btn btn--primary" disabled={busy || !title.trim() || !advisory.trim()}>
          {busy ? "Authoring…" : "Author rule"}
        </button>
      </form>
      {error ? (
        <div className="notice notice--danger" style={{ marginTop: 12 }}>{error}</div>
      ) : null}
      {result ? (
        <>
          <h3>{result.valid ? "Valid rule" : "Invalid — not usable as-is"}</h3>
          <pre className="output output--code">{result.rule}</pre>
          {result.errors.length > 0 ? (
            <div className="notice notice--danger">{result.errors.join("; ")}</div>
          ) : null}
          {result.warnings.length > 0 ? <p>{result.warnings.join("; ")}</p> : null}
        </>
      ) : null}
    </>
  );
}

export function IntelWorkbench() {
  const [tab, setTab] = useState<Tab>("extract");

  return (
    <>
      <h1>Cyber Intelligence</h1>
      <p>Turn advisories into indicators, prioritise vulnerabilities, and author detection rules.</p>

      <div className="seg" style={{ marginBottom: 16 }}>
        <button type="button" aria-pressed={tab === "extract"} onClick={() => setTab("extract")}>
          CTI Extract
        </button>
        <button type="button" aria-pressed={tab === "vuln"} onClick={() => setTab("vuln")}>
          Vulnerability
        </button>
        <button type="button" aria-pressed={tab === "detect"} onClick={() => setTab("detect")}>
          Detections
        </button>
      </div>

      {tab === "extract" ? <ExtractPanel /> : null}
      {tab === "vuln" ? <VulnPanel /> : null}
      {tab === "detect" ? <DetectPanel /> : null}
    </>
  );
}
