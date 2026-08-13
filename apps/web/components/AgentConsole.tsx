"use client";

import { useState } from "react";

interface Step {
  index: number;
  thought: string;
  tool: string;
  side_effect: string;
  permitted: boolean | null;
  permission_reason: string;
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
  agent: string;
  goal: string;
  state: string;
  result: string | null;
  error: string | null;
  steps: Step[];
  pending_approval: PendingApproval | null;
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

function StepRow({ s }: { s: Step }) {
  const status = s.executed_ok === true ? "✓ ran" : s.permitted === false ? "✗ denied" : "…";
  return (
    <li>
      <code>{s.tool || "(finish)"}</code>{" "}
      <span style={{ color: "#666" }}>[{s.side_effect}]</span> — {s.thought}{" "}
      <strong>{status}</strong>
      {s.permitted === false ? (
        <div style={{ color: "#b00020", fontSize: "0.8rem" }}>{s.permission_reason}</div>
      ) : null}
    </li>
  );
}

export function AgentConsole() {
  const [goal, setGoal] = useState("Investigate the outbound beacon alert");
  const [run, setRun] = useState<Run | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function call(path: string, body: unknown): Promise<void> {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = (await res.json()) as Run & { detail?: string };
      if (!res.ok) {
        throw new Error(data.detail ?? `request failed (${res.status})`);
      }
      setRun(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  const start = () => call("/api/agents/runs", { agent: "investigation-assistant", goal });
  const decide = (approved: boolean) =>
    run ? call(`/api/agents/runs/${run.run_id}/approval`, { approved }) : undefined;

  return (
    <main>
      <h1>Investigation Agent</h1>
      <p>
        A read-first SOC agent (Phase 06). It triages, enriches, and corroborates with read-only
        tools; any consequential action pauses for your approval.
      </p>

      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
        <input
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          style={{ flex: 1, padding: "0.5rem" }}
          placeholder="Investigation goal"
        />
        <button onClick={start} disabled={busy || !goal.trim()}>
          {busy ? "Running…" : "Start investigation"}
        </button>
      </div>

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

          {run.result ? (
            <>
              <h3>Result</h3>
              <pre style={preStyle}>{run.result}</pre>
            </>
          ) : null}
          {run.error ? <p style={{ color: "#b00020" }}>Halted: {run.error}</p> : null}
        </>
      ) : null}
    </main>
  );
}
