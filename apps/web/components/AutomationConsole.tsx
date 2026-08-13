"use client";

import { useEffect, useState } from "react";

interface PlaybookStep {
  id: string;
  tool: string;
  description: string;
}

interface Playbook {
  name: string;
  title: string;
  description: string;
  base_agent: string;
  tags: string[];
  steps: PlaybookStep[];
}

interface RunStep {
  index: number;
  thought: string;
  tool: string;
  side_effect: string;
  permitted: boolean | null;
  approved: boolean | null;
  executed_ok: boolean | null;
}

interface PendingApproval {
  step: number;
  tool: string;
  args: Record<string, unknown>;
  impact: string;
}

interface Run {
  run_id: string;
  playbook: string;
  goal: string;
  state: string;
  result: string | null;
  error: string | null;
  steps: RunStep[];
  pending_approval: PendingApproval | null;
}

interface Evidence {
  ref: string;
  kind: string;
  summary: string;
  untrusted: boolean;
}

interface Report {
  run_id: string;
  title: string;
  state: string;
  outcome: string;
  executive_summary: string;
  technical_detail: string;
  evidence: Evidence[];
  markdown: string;
}

const preStyle = {
  background: "#0b0b0b",
  color: "#e6e6e6",
  padding: "0.75rem",
  borderRadius: 8,
  whiteSpace: "pre-wrap" as const,
  fontSize: "0.8rem",
};

const stateColor: Record<string, string> = {
  completed: "#137333",
  halted: "#b00020",
  failed: "#b00020",
  awaiting_approval: "#a15c00",
};

function StepRow({ s }: { s: RunStep }) {
  const status = s.executed_ok === true ? "✓ ran" : s.permitted === false ? "✗ denied" : "…";
  return (
    <li>
      <code>{s.tool || "(finish)"}</code>{" "}
      <span style={{ color: "#666" }}>[{s.side_effect}]</span> — {s.thought}{" "}
      <strong>{status}</strong>
    </li>
  );
}

export function AutomationConsole() {
  const [playbooks, setPlaybooks] = useState<Playbook[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [run, setRun] = useState<Run | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    void (async () => {
      try {
        const res = await fetch("/api/automation/playbooks");
        const data = (await res.json()) as Playbook[];
        if (Array.isArray(data)) {
          setPlaybooks(data);
          if (data[0]) setSelected(data[0].name);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      }
    })();
  }, []);

  async function call(path: string, body?: unknown): Promise<Run | null> {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body ?? {}),
      });
      const data = (await res.json()) as Run & { detail?: string };
      if (!res.ok) throw new Error(data.detail ?? `request failed (${res.status})`);
      setRun(data);
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      return null;
    } finally {
      setBusy(false);
    }
  }

  const start = () => {
    setReport(null);
    return call(`/api/automation/playbooks/${selected}/runs`, { goal: "" });
  };
  const decide = (approved: boolean) =>
    run ? call(`/api/automation/runs/${run.run_id}/approval`, { approved }) : undefined;

  async function loadReport(): Promise<void> {
    if (!run) return;
    setBusy(true);
    try {
      const res = await fetch(`/api/automation/runs/${run.run_id}/report`);
      const data = (await res.json()) as Report;
      if (res.ok) setReport(data);
    } finally {
      setBusy(false);
    }
  }

  const active = playbooks.find((p) => p.name === selected);

  return (
    <main>
      <h1>Automation Playbooks</h1>
      <p>
        Supervised, declarative security playbooks (Phase 08). Each runs on the agent runtime, so
        read-only steps run automatically and consequential steps pause for your approval — no
        action is ever taken without authorization.
      </p>

      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.5rem" }}>
        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          style={{ flex: 1, padding: "0.5rem" }}
        >
          {playbooks.map((p) => (
            <option key={p.name} value={p.name}>
              {p.title}
            </option>
          ))}
        </select>
        <button onClick={start} disabled={busy || !selected}>
          {busy ? "Running…" : "Run playbook"}
        </button>
      </div>

      {active ? (
        <p style={{ color: "#555", fontSize: "0.85rem" }}>
          {active.description} <em>Steps: {active.steps.map((s) => s.tool).join(" → ")}</em>
        </p>
      ) : null}

      {error ? <p style={{ color: "#b00020" }}>{error}</p> : null}

      {run ? (
        <>
          <h2>
            Run <code>{run.run_id.slice(0, 8)}</code> —{" "}
            <span style={{ color: stateColor[run.state] ?? "#333" }}>{run.state}</span>
          </h2>

          {run.pending_approval ? (
            <div
              style={{
                border: "1px solid #a15c00",
                borderRadius: 8,
                padding: "0.75rem",
                marginBottom: "1rem",
              }}
            >
              <strong>Approval required:</strong> {run.pending_approval.impact}
              <div style={{ marginTop: "0.5rem" }}>
                <button onClick={() => decide(true)} disabled={busy}>
                  Approve
                </button>{" "}
                <button onClick={() => decide(false)} disabled={busy}>
                  Reject
                </button>
              </div>
            </div>
          ) : null}

          <h3>Trace</h3>
          <ol>
            {run.steps.map((s) => (
              <StepRow key={s.index} s={s} />
            ))}
          </ol>

          {run.error ? <p style={{ color: "#b00020" }}>Halted: {run.error}</p> : null}

          <button onClick={loadReport} disabled={busy}>
            Generate report
          </button>

          {report ? (
            <>
              <h3>{report.title}</h3>
              <p>
                <strong>Outcome:</strong> {report.outcome}
              </p>
              <pre style={preStyle}>{report.markdown}</pre>
            </>
          ) : null}
        </>
      ) : null}
    </main>
  );
}
