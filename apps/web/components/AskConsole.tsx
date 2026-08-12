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

const preStyle = {
  background: "#0b0b0b",
  color: "#e6e6e6",
  padding: "1rem",
  borderRadius: 8,
  whiteSpace: "pre-wrap" as const,
  minHeight: "3rem",
};

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
  const [busy, setBusy] = useState(false);

  function reset() {
    setAnswer("");
    setCitations([]);
    setGrounded(null);
  }

  async function askStreaming() {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    if (!res.ok || !res.body) {
      setAnswer(`Error: ${res.status}`);
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
      setAnswer(`Error: ${res.status}`);
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
    } finally {
      setBusy(false);
    }
  }

  return (
    <main>
      <h1>Ask Dula</h1>
      <p>Grounded, cited answers over your security knowledge (Phase 03 — general model).</p>

      <div style={{ marginBottom: "1rem" }}>
        <label style={{ marginRight: "1rem" }}>
          <input
            type="radio"
            checked={mode === "question"}
            onChange={() => setMode("question")}
          />{" "}
          Question
        </label>
        <label>
          <input type="radio" checked={mode === "triage"} onChange={() => setMode("triage")} />{" "}
          Triage alert
        </label>
      </div>

      <form onSubmit={onSubmit}>
        {mode === "question" ? (
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            rows={3}
            placeholder="e.g. How do I defend against brute force attacks?"
            style={{ width: "100%", padding: "0.5rem" }}
          />
        ) : (
          <div style={{ display: "grid", gap: "0.5rem" }}>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Alert title"
              style={{ padding: "0.5rem" }}
            />
            <select value={severity} onChange={(e) => setSeverity(e.target.value)}>
              <option value="low">low</option>
              <option value="medium">medium</option>
              <option value="high">high</option>
              <option value="critical">critical</option>
            </select>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              placeholder="Alert details (optional)"
              style={{ padding: "0.5rem" }}
            />
          </div>
        )}
        <button type="submit" disabled={busy} style={{ marginTop: "0.75rem" }}>
          {busy ? "Thinking…" : "Ask"}
        </button>
      </form>

      <h2>Answer {grounded === false ? "(ungrounded)" : grounded ? "(grounded)" : ""}</h2>
      <pre style={preStyle}>{answer || "—"}</pre>

      {citations.length > 0 ? (
        <>
          <h3>Evidence</h3>
          <ol>
            {citations.map((c) => (
              <li key={c.marker}>
                <strong>[{c.marker}]</strong> <em>{c.source}</em> — {c.snippet}
              </li>
            ))}
          </ol>
        </>
      ) : null}
    </main>
  );
}
