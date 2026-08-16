// Minimal Markdown renderer for grounded reports (docs/13-Agents/Playbooks.md §5).
//
// SECURITY: report bodies embed **untrusted tool output** (log lines, indicator values, ticket
// titles). HTML is therefore escaped FIRST and markup is generated only from our own patterns
// afterwards, so no attacker-controlled string can introduce an element or attribute. Raw HTML
// in the source is intentionally not supported.
//
// Scope is deliberately the subset the report generator emits: headings, tables, blockquotes,
// unordered lists, bold, and inline code. Anything else renders as plain text.

function escapeHtml(input: string): string {
  return input
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function inline(escaped: string): string {
  return escaped
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
}

function isTableRow(line: string): boolean {
  return line.trim().startsWith("|") && line.trim().endsWith("|");
}

function cells(line: string): string[] {
  return line
    .trim()
    .slice(1, -1)
    .split("|")
    .map((c) => c.trim());
}

const DIVIDER = /^\s*\|?[\s:-]*-[\s:|-]*\|?\s*$/;

export function renderMarkdown(source: string): string {
  const lines = escapeHtml(source).split("\n");
  const out: string[] = [];
  let i = 0;
  let inList = false;

  const closeList = () => {
    if (inList) {
      out.push("</ul>");
      inList = false;
    }
  };

  while (i < lines.length) {
    const line = lines[i] ?? "";

    // Table: a header row, a divider, then body rows.
    if (isTableRow(line) && DIVIDER.test(lines[i + 1] ?? "")) {
      closeList();
      out.push("<table><thead><tr>");
      cells(line).forEach((c) => out.push(`<th>${inline(c)}</th>`));
      out.push("</tr></thead><tbody>");
      i += 2;
      while (i < lines.length && isTableRow(lines[i] ?? "")) {
        out.push("<tr>");
        cells(lines[i] ?? "").forEach((c) => out.push(`<td>${inline(c)}</td>`));
        out.push("</tr>");
        i += 1;
      }
      out.push("</tbody></table>");
      continue;
    }

    const heading = /^(#{1,4})\s+(.*)$/.exec(line);
    if (heading) {
      closeList();
      const level = Math.min((heading[1] ?? "#").length + 1, 6); // report h1 -> page h2
      out.push(`<h${level}>${inline(heading[2] ?? "")}</h${level}>`);
      i += 1;
      continue;
    }

    if (/^&gt;\s?/.test(line)) {
      closeList();
      out.push(`<blockquote>${inline(line.replace(/^&gt;\s?/, ""))}</blockquote>`);
      i += 1;
      continue;
    }

    if (/^[-*]\s+/.test(line)) {
      if (!inList) {
        out.push("<ul>");
        inList = true;
      }
      out.push(`<li>${inline(line.replace(/^[-*]\s+/, ""))}</li>`);
      i += 1;
      continue;
    }

    if (line.trim() === "") {
      closeList();
      i += 1;
      continue;
    }

    closeList();
    out.push(`<p>${inline(line)}</p>`);
    i += 1;
  }

  closeList();
  return out.join("\n");
}
