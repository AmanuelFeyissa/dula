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

const preStyle = {
  background: "#0b0b0b",
  color: "#e6e6e6",
  padding: "1rem",
  borderRadius: 8,
  whiteSpace: "pre-wrap" as const,
  minHeight: "3rem",
  fontSize: "0.85rem",
};

const tabStyle = (active: boolean) => ({
  padding: "0.4rem 0.9rem",
  marginRight: "0.5rem",
  borderRadius: 6,
  border: "1px solid #ccc",
  background: active ? "#222" : "transparent",
  color: active ? "#fff" : "inherit",
  cursor: "pointer",
});

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
          style={{ width: "100%", padding: "0.5rem" }}
        />
        <button type="submit" disabled={busy || !advisory.trim()} style={{ marginTop: "0.75rem" }}>
          {busy ? "Extracting…" : "Extract"}
        </button>
      </form>
      {error ? <p style={{ color: "#c00" }}>{error}</p> : null}
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
              <pre style={preStyle}>{result.summary}</pre>
            </>
          ) : null}
          <h3>STIX 2.1 Bundle</h3>
          <pre style={preStyle}>{JSON.stringify(result.stix_bundle, null, 2)}</pre>
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
      <form onSubmit={run} style={{ display: "grid", gap: "0.5rem", maxWidth: 480 }}>
        <input
          value={vector}
          onChange={(e) => setVector(e.target.value)}
          placeholder="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
          style={{ padding: "0.5rem" }}
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
        <button type="submit" disabled={busy} style={{ width: "fit-content" }}>
          {busy ? "Scoring…" : "Analyze"}
        </button>
      </form>
      {error ? <p style={{ color: "#c00" }}>{error}</p> : null}
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
      <form onSubmit={run} style={{ display: "grid", gap: "0.5rem" }}>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder={format === "sigma" ? "Rule title" : "Rule name (identifier)"}
          style={{ padding: "0.5rem" }}
        />
        <textarea
          value={advisory}
          onChange={(e) => setAdvisory(e.target.value)}
          rows={4}
          placeholder="Advisory text containing the indicators to detect…"
          style={{ padding: "0.5rem" }}
        />
        <button type="submit" disabled={busy || !title.trim() || !advisory.trim()}>
          {busy ? "Authoring…" : "Author rule"}
        </button>
      </form>
      {error ? <p style={{ color: "#c00" }}>{error}</p> : null}
      {result ? (
        <>
          <h3>{result.valid ? "Valid rule" : "Invalid — not usable as-is"}</h3>
          <pre style={preStyle}>{result.rule}</pre>
          {result.errors.length > 0 ? (
            <p style={{ color: "#c00" }}>{result.errors.join("; ")}</p>
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
    <main>
      <h1>Cyber Intelligence</h1>
      <p>CTI extraction, vulnerability prioritization, and detection authoring (Phase 05).</p>

      <div style={{ marginBottom: "1rem" }}>
        <button style={tabStyle(tab === "extract")} onClick={() => setTab("extract")}>
          CTI Extract
        </button>
        <button style={tabStyle(tab === "vuln")} onClick={() => setTab("vuln")}>
          Vulnerability
        </button>
        <button style={tabStyle(tab === "detect")} onClick={() => setTab("detect")}>
          Detections
        </button>
      </div>

      {tab === "extract" ? <ExtractPanel /> : null}
      {tab === "vuln" ? <VulnPanel /> : null}
      {tab === "detect" ? <DetectPanel /> : null}
    </main>
  );
}
