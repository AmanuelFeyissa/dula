"use client";

import { useEffect, useState } from "react";

import { renderMarkdown } from "@/lib/markdown";

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

const STATE_TONE: Record<string, string> = {
  completed: "chip--ok",
  halted: "chip--critical",
  failed: "chip--critical",
  awaiting_approval: "chip--medium",
};

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
        if (!res.ok) {
          throw new Error(
            res.status === 401
              ? "Your session expired — sign in again."
              : `Couldn't load playbooks (${res.status})`,
          );
        }
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

  async function call(path: string, body?: unknown): Promise<void> {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body ?? {}),
      });
      const data = (await res.json()) as Run & { detail?: string };
      if (!res.ok) throw new Error(data.detail ?? `Request failed (${res.status})`);
      setRun(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
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
    setError(null);
    try {
      const res = await fetch(`/api/automation/runs/${run.run_id}/report`);
      if (!res.ok) throw new Error(`Couldn't build the report (${res.status})`);
      setReport((await res.json()) as Report);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  const active = playbooks.find((p) => p.name === selected);

  return (
    <>
      <header className="page__head">
        <h1>Playbooks</h1>
        <p className="page__desc">
          Saved procedures that run on the agent runtime. Read-only steps run automatically;
          consequential steps stop for your approval.
        </p>
      </header>

      <div className="card" style={{ marginBottom: 18 }}>
        <label
          htmlFor="playbook"
          className="faint"
          style={{ fontSize: 12, display: "block", marginBottom: 6 }}
        >
          Playbook
        </label>
        <div className="field">
          <select
            id="playbook"
            className="select"
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
          >
            {playbooks.map((p) => (
              <option key={p.name} value={p.name}>
                {p.title}
              </option>
            ))}
          </select>
          <button className="btn btn--primary" onClick={start} disabled={busy || !selected}>
            {busy ? "Running…" : "Run playbook"}
          </button>
        </div>
        {active ? (
          <>
            <p className="muted" style={{ margin: "10px 0 8px", fontSize: 13.5 }}>
              {active.description}
            </p>
            <div className="row" style={{ gap: 6 }}>
              {active.steps.map((s, i) => (
                <span key={s.id} className="row" style={{ gap: 6 }}>
                  <span className="chip chip--info mono" style={{ fontSize: 11 }}>
                    {s.tool}
                  </span>
                  {i < active.steps.length - 1 ? <span className="faint">→</span> : null}
                </span>
              ))}
            </div>
          </>
        ) : null}
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
            </div>
          ) : null}

          <div className="panel">
            <ol className="trace">
              {run.steps.map((s) => (
                <li key={s.index} className="trace__item">
                  <span className="trace__idx">{s.index + 1}</span>
                  <span>
                    <span className="trace__tool">{s.tool || "(finish)"}</span>{" "}
                    {s.side_effect === "consequential" ? (
                      <span className="chip chip--medium" style={{ fontSize: 11 }}>
                        Consequential
                      </span>
                    ) : null}
                    <div className="trace__thought">{s.thought}</div>
                    {/* Attribution belongs next to the action: a consequential step is only
                        accountable if the trace says who let it through. */}
                    {s.approved !== null && s.approved_by ? (
                      <div
                        style={{ color: "var(--text-muted)", fontSize: 12.5, marginTop: 2 }}
                      >
                        {s.approved ? "Approved" : "Rejected"} by {s.approved_by}
                      </div>
                    ) : null}
                  </span>
                  <span
                    className={`chip ${
                      s.executed_ok
                        ? "chip--ok"
                        : s.permitted === false
                          ? "chip--critical"
                          : "chip--medium"
                    }`}
                  >
                    {s.executed_ok ? "Ran" : s.permitted === false ? "Refused" : "Waiting"}
                  </span>
                </li>
              ))}
            </ol>
          </div>

          {run.error ? (
            <div className="notice notice--warn">
              <div className="notice__title">Run halted</div>
              <div className="muted">{run.error}</div>
            </div>
          ) : null}

          {run.state === "completed" || run.state === "halted" ? (
            <div>
              <button className="btn" onClick={loadReport} disabled={busy}>
                {report ? "Refresh report" : "Generate report"}
              </button>
            </div>
          ) : null}

          {report ? (
            <div className="card">
              <div className="row" style={{ justifyContent: "space-between", marginBottom: 10 }}>
                <h2 style={{ margin: 0 }}>{report.title}</h2>
                <button
                  className="btn btn--ghost"
                  onClick={() => void navigator.clipboard?.writeText(report.markdown)}
                >
                  Copy Markdown
                </button>
              </div>
              {/* Rendered from Markdown; the renderer escapes HTML first because report bodies
                  embed untrusted tool output. The leading `# title` is dropped — the card
                  header already carries it, and repeating it reads like a bug. */}
              <div
                className="report"
                dangerouslySetInnerHTML={{
                  __html: renderMarkdown(report.markdown.replace(/^#\s+.*\n/, "")),
                }}
              />
            </div>
          ) : null}
        </div>
      ) : null}
    </>
  );
}
