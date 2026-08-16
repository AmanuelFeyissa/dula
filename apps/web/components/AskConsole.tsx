"use client";

import { useState } from "react";

interface Citation {
  marker: number;
  source: string;
  document_id: string;
  snippet: string;
}

interface AnswerPayload {
  answer: string;
  grounded: boolean;
  model: string;
  citations: Citation[];
}

type Mode = "question" | "triage";

function parseSse(chunk: string, onToken: (t: string) => void, onDone: (p: AnswerPayload) => void) {
  for (const block of chunk.split("\n\n")) {
    if (!block.trim()) continue;
    let event = "message";
    let data = "";
    for (const line of block.split("\n")) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      else if (line.startsWith("data:")) data += line.slice(5).trim();
    }
    if (!data) continue;
    if (event === "done") onDone(JSON.parse(data) as AnswerPayload);
    else {
      const parsed = JSON.parse(data) as { token?: string };
      if (parsed.token) onToken(parsed.token);
    }
  }
}

export function AskConsole() {
  const [mode, setMode] = useState<Mode>("question");
  const [question, setQuestion] = useState("");
  const [title, setTitle] = useState("");
  const [severity, setSeverity] = useState("medium");
  const [description, setDescription] = useState("");
  const [answer, setAnswer] = useState("");
  const [citations, setCitations] = useState<Citation[]>([]);
  const [grounded, setGrounded] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function reset() {
    setAnswer("");
    setCitations([]);
    setGrounded(null);
    setError(null);
  }

  function failure(status: number): string {
    return status === 401
      ? "Your session expired — sign in again."
      : `The AI Gateway returned ${status}.`;
  }

  async function askStreaming() {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    if (!res.ok || !res.body) {
      setError(failure(res.status));
      return;
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split("\n\n");
      buffer = blocks.pop() ?? "";
      parseSse(
        blocks.join("\n\n"),
        (t) => setAnswer((a) => a + t),
        (p) => {
          setAnswer(p.answer);
          setCitations(p.citations);
          setGrounded(p.grounded);
        },
      );
    }
  }

  async function triage() {
    const res = await fetch("/api/triage", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, severity, description: description || null }),
    });
    if (!res.ok) {
      setError(failure(res.status));
      return;
    }
    const payload = (await res.json()) as AnswerPayload;
    setAnswer(payload.answer);
    setCitations(payload.citations);
    setGrounded(payload.grounded);
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    reset();
    setBusy(true);
    try {
      if (mode === "question") await askStreaming();
      else await triage();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  const canSubmit = mode === "question" ? question.trim().length > 0 : title.trim().length > 0;

  return (
    <>
      <header className="page__head">
        <h1>Ask Dula</h1>
        <p className="page__desc">
          Answers grounded in your security knowledge base, with the evidence they came from.
        </p>
      </header>

      <form onSubmit={onSubmit} className="card" style={{ marginBottom: 18 }}>
        <div className="seg" style={{ marginBottom: 12 }}>
          <button
            type="button"
            aria-pressed={mode === "question"}
            onClick={() => setMode("question")}
          >
            Ask a question
          </button>
          <button type="button" aria-pressed={mode === "triage"} onClick={() => setMode("triage")}>
            Triage an alert
          </button>
        </div>

        {mode === "question" ? (
          <textarea
            className="textarea"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            rows={3}
            placeholder="e.g. How do I defend against brute force attacks?"
          />
        ) : (
          <div className="stack" style={{ gap: 10 }}>
            <input
              className="input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Alert title"
            />
            <select
              className="select"
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
              aria-label="Severity"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
            <textarea
              className="textarea"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              placeholder="Alert details (optional)"
            />
          </div>
        )}

        <button
          type="submit"
          className="btn btn--primary"
          disabled={busy || !canSubmit}
          style={{ marginTop: 12 }}
        >
          {busy ? "Thinking…" : mode === "question" ? "Ask" : "Triage"}
        </button>
      </form>

      {error ? (
        <div className="notice notice--danger" style={{ marginBottom: 18 }}>
          <div className="notice__title">Couldn&apos;t get an answer</div>
          <div className="muted">{error}</div>
        </div>
      ) : null}

      {answer || busy ? (
        <section className="stack">
          <div className="row" style={{ justifyContent: "space-between" }}>
            <h2 style={{ margin: 0 }}>Answer</h2>
            {grounded !== null ? (
              <span className={`chip ${grounded ? "chip--ok" : "chip--medium"}`}>
                {grounded ? "Grounded in evidence" : "No supporting evidence"}
              </span>
            ) : null}
          </div>
          <div className="output output--prose">
            {answer || <span className="faint">Thinking…</span>}
          </div>

          {citations.length > 0 ? (
            <div>
              <h3>Evidence</h3>
              <ul className="evidence">
                {citations.map((c) => (
                  <li key={c.marker}>
                    <span className="cite">[{c.marker}]</span>
                    <span>
                      <strong>{c.source}</strong>
                      <div className="muted">{c.snippet}</div>
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </section>
      ) : null}
    </>
  );
}
