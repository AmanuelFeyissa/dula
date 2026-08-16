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
  /** Who decided. Optional: null until a decision exists. */
  approved_by: string | null;
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

const STATE_TONE: Record<string, string> = {
  completed: "chip--ok",
  halted: "chip--critical",
  failed: "chip--critical",
  awaiting_approval: "chip--medium",
  executing: "chip--accent",
  planning: "chip--accent",
};

function StepRow({ s }: { s: Step }) {
  const outcome =
    s.executed_ok === true
      ? { label: "Ran", cls: "chip--ok" }
      : s.permitted === false
        ? { label: "Refused", cls: "chip--critical" }
        : s.approved === false
          ? { label: "Rejected", cls: "chip--critical" }
          : { label: "Waiting", cls: "chip--medium" };

  return (
    <li className="trace__item">
      <span className="trace__idx">{s.index + 1}</span>
      <span>
        <span className="trace__tool">{s.tool || "(finish)"}</span>{" "}
        {s.side_effect === "consequential" ? (
          <span className="chip chip--medium" style={{ fontSize: 11 }}>
            Consequential
          </span>
        ) : (
          <span className="chip chip--info" style={{ fontSize: 11 }}>
            Read-only
          </span>
        )}
        <div className="trace__thought">{s.thought}</div>
        {s.permitted === false && s.permission_reason ? (
          <div style={{ color: "var(--sev-critical)", fontSize: 12.5, marginTop: 2 }}>
            {s.permission_reason}
          </div>
        ) : null}
        {/* Attribution belongs next to the action, not buried in the report: a consequential
            step is only accountable if the trace says who let it through. */}
        {s.approved !== null && s.approved_by ? (
          <div style={{ color: "var(--text-muted)", fontSize: 12.5, marginTop: 2 }}>
            {s.approved ? "Approved" : "Rejected"} by {s.approved_by}
          </div>
        ) : null}
      </span>
      <span className={`chip ${outcome.cls}`}>{outcome.label}</span>
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
        throw new Error(data.detail ?? `Request failed (${res.status})`);
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
    <>
      <header className="page__head">
        <h1>Investigation agent</h1>
        <p className="page__desc">
          A read-first SOC agent. It triages, enriches, and corroborates on its own; anything
          consequential stops and waits for you.
        </p>
      </header>

      <div className="card" style={{ marginBottom: 18 }}>
        <label
          htmlFor="goal"
          className="faint"
          style={{ fontSize: 12, display: "block", marginBottom: 6 }}
        >
          What should it investigate?
        </label>
        <div className="field">
          <input
            id="goal"
            className="input"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="e.g. Investigate the outbound beacon alert"
          />
          <button className="btn btn--primary" onClick={start} disabled={busy || !goal.trim()}>
            {busy ? "Working…" : "Start investigation"}
          </button>
        </div>
      </div>

      {error ? (
        <div className="notice notice--danger" style={{ marginBottom: 18 }}>
          <div className="notice__title">That didn&apos;t work</div>
          <div className="muted">{error}</div>
        </div>
      ) : null}

      {run ? (
        <div className="stack">
          <div className="row" style={{ justifyContent: "space-between" }}>
            <h2 style={{ margin: 0 }}>Run</h2>
            <span className="row" style={{ gap: 8 }}>
              <span className={`chip ${STATE_TONE[run.state] ?? "chip--info"}`}>
                {run.state.replace(/_/g, " ")}
              </span>
              <code className="mono faint">{run.run_id.slice(0, 8)}</code>
            </span>
          </div>

          {run.pending_approval ? (
            <div className="gate">
              <div className="gate__eyebrow">Your approval is required</div>
              <div className="gate__impact">{run.pending_approval.impact}</div>
              <div className="row">
                <button className="btn btn--primary" onClick={() => decide(true)} disabled={busy}>
                  Approve and continue
                </button>
                <button className="btn btn--danger" onClick={() => decide(false)} disabled={busy}>
                  Reject
                </button>
              </div>
              <p className="faint" style={{ margin: "10px 0 0", fontSize: 12.5 }}>
                Nothing happens until you choose. Rejecting halts the run without taking the action.
              </p>
            </div>
          ) : null}

          <div className="panel">
            <ol className="trace">
              {run.steps.map((s) => (
                <StepRow key={s.index} s={s} />
              ))}
            </ol>
          </div>

          {run.error ? (
            <div className="notice notice--warn">
              <div className="notice__title">Run halted</div>
              <div className="muted">{run.error}</div>
            </div>
          ) : null}

          {run.result ? (
            <div>
              <h3>Result</h3>
              <div className="output output--prose">{run.result}</div>
            </div>
          ) : null}
        </div>
      ) : null}
    </>
  );
}
