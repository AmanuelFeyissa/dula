import Link from "next/link";
import type { CSSProperties, ReactNode } from "react";

// Shared presentation primitives. Severity and state are the two things an analyst scans for,
// so they get one canonical rendering everywhere (globals.css owns the palette).

const SEVERITIES = ["critical", "high", "medium", "low", "info"] as const;
type Severity = (typeof SEVERITIES)[number];

function severityTone(value: string | null | undefined): Severity {
  const v = (value ?? "").toLowerCase();
  return (SEVERITIES as readonly string[]).includes(v) ? (v as Severity) : "info";
}

/** Machine enum -> human label: `in_progress` should read as "In progress", not as raw data. */
export function humanize(value: string | null | undefined): string {
  if (!value) return "—";
  const s = value.replace(/[_-]+/g, " ").trim();
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/** Severity as colour + label. Colour is never the only signal (WCAG 1.4.1). */
export function SeverityChip({ value }: { value: string | null | undefined }) {
  const tone = severityTone(value);
  return (
    <span className={`chip chip--${tone}`} title={`Severity: ${humanize(value)}`}>
      <span className="chip__dot" aria-hidden="true" />
      {humanize(value)}
    </span>
  );
}

/** Workflow state. Resolved/closed states recede; active work stays legible. */
export function StatusChip({ value }: { value: string | null | undefined }) {
  const v = (value ?? "").toLowerCase();
  const tone =
    v === "closed" || v === "resolved" || v === "false_positive"
      ? "info"
      : v === "new" || v === "open"
        ? "accent"
        : "ok";
  return <span className={`chip chip--${tone}`}>{humanize(value)}</span>;
}

export function spineClass(severity: string | null | undefined): string {
  return `spine spine--${severityTone(severity)}`;
}

/** Absolute timestamps are unreadable at a glance; relative ones answer "is this happening now?". */
export function RelativeTime({ iso }: { iso: string | null | undefined }) {
  if (!iso) return <span className="faint">—</span>;
  const then = new Date(iso);
  if (Number.isNaN(then.getTime())) return <span className="faint">—</span>;

  const seconds = Math.round((Date.now() - then.getTime()) / 1000);
  const label =
    seconds < 60
      ? "just now"
      : seconds < 3600
        ? `${Math.floor(seconds / 60)}m ago`
        : seconds < 86400
          ? `${Math.floor(seconds / 3600)}h ago`
          : `${Math.floor(seconds / 86400)}d ago`;

  return (
    <time dateTime={iso} title={then.toLocaleString()} className="faint">
      {label}
    </time>
  );
}

export function PageHeader({
  title,
  description,
  aside,
}: {
  title: string;
  description?: string;
  aside?: ReactNode;
}) {
  return (
    <header className="page__head">
      <div className="row" style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h1>{title}</h1>
          {description ? <p className="page__desc">{description}</p> : null}
        </div>
        {aside}
      </div>
    </header>
  );
}

// --- List controls: filter, sort, paginate ------------------------------------------
//
// Filter/sort/page state lives entirely in the URL (?severity=critical&sort=-severity&
// offset=50), never in component state. A filtered SOC view has to be linkable in a
// handoff, and a server component can only see state that arrived in the request.

/** The shape Next.js hands a server component's page for `?query=params`. */
export type SearchParams = Record<string, string | string[] | undefined>;

function str(value: string | string[] | undefined): string {
  return typeof value === "string" ? value : "";
}

/** Merge `overrides` into `params`; a `null` override removes that key (e.g. resetting
 *  `offset` when a filter or sort changes, since the old page number is no longer meaningful). */
function withQuery(params: SearchParams, overrides: Record<string, string | number | null>): string {
  const merged = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (typeof value === "string" && value !== "") merged.set(key, value);
  }
  for (const [key, value] of Object.entries(overrides)) {
    if (value === null || value === "") merged.delete(key);
    else merged.set(key, String(value));
  }
  const qs = merged.toString();
  return qs ? `?${qs}` : "";
}

export interface FilterField {
  name: string;
  label: string;
  options: readonly string[];
}

/**
 * A plain GET form, not a client component: it works with JavaScript disabled, and the
 * browser's native back/forward history does the right thing without any code for it.
 * `humanize` renders option labels, so `false_positive` reads as "False positive" here too.
 */
export function FilterBar({
  basePath,
  searchParams,
  filters,
}: {
  basePath: string;
  searchParams: SearchParams;
  filters: FilterField[];
}) {
  const q = str(searchParams.q);
  const hasActiveFilter = q !== "" || filters.some((f) => str(searchParams[f.name]) !== "");

  return (
    <form className="filterbar" method="GET" action={basePath}>
      <input
        type="search"
        name="q"
        defaultValue={q}
        placeholder="Search…"
        aria-label="Search"
        className="input filterbar__search"
      />
      {filters.map((f) => (
        <select
          key={f.name}
          name={f.name}
          defaultValue={str(searchParams[f.name])}
          aria-label={f.label}
          className="select"
        >
          <option value="">All {f.label.toLowerCase()}</option>
          {f.options.map((o) => (
            <option key={o} value={o}>
              {humanize(o)}
            </option>
          ))}
        </select>
      ))}
      <button type="submit" className="btn btn--primary">
        Filter
      </button>
      {hasActiveFilter ? (
        <Link href={basePath} className="btn btn--ghost">
          Clear
        </Link>
      ) : null}
    </form>
  );
}

/**
 * A column header that is also a sort control. Clicking toggles ascending -> descending on
 * that field (a different field starts ascending); changing sort always resets `offset` to
 * 0, because "page 3 sorted by title" is not a page that existed under the old sort.
 */
export function SortableHeader({
  basePath,
  searchParams,
  field,
  label,
  style,
}: {
  basePath: string;
  searchParams: SearchParams;
  field: string;
  label: string;
  style?: CSSProperties;
}) {
  const current = str(searchParams.sort);
  const isActive = current === field || current === `-${field}`;
  const next = current === field ? `-${field}` : field;
  const href = `${basePath}${withQuery(searchParams, { sort: next, offset: null })}`;

  return (
    <th style={style}>
      <Link href={href} className={isActive ? "th-sort th-sort--active" : "th-sort"}>
        {label}
        {isActive ? (
          <span className="th-sort__arrow" aria-hidden="true">
            {current.startsWith("-") ? "▼" : "▲"}
          </span>
        ) : null}
        <span className="sr-only">
          {isActive
            ? `, sorted ${current.startsWith("-") ? "descending" : "ascending"}`
            : ", not sorted"}
        </span>
      </Link>
    </th>
  );
}

/** Prev/Next over the limit/offset page envelope every list endpoint returns. Renders
 *  nothing when everything already fits on one page — pagination controls for a page that
 *  can't go anywhere are just clutter. */
export function Pagination({
  basePath,
  searchParams,
  limit,
  offset,
  total,
}: {
  basePath: string;
  searchParams: SearchParams;
  limit: number;
  offset: number;
  total: number;
}) {
  if (total <= limit && offset === 0) return null;

  const page = Math.floor(offset / limit) + 1;
  const pageCount = Math.max(1, Math.ceil(total / limit));
  const prevOffset = Math.max(0, offset - limit);
  const nextOffset = offset + limit;
  const hasPrev = offset > 0;
  const hasNext = nextOffset < total;

  return (
    <nav className="pagination" aria-label="Pagination">
      {hasPrev ? (
        <Link href={`${basePath}${withQuery(searchParams, { offset: prevOffset || null })}`} className="btn btn--ghost">
          ← Previous
        </Link>
      ) : (
        <span className="btn btn--ghost" aria-disabled="true">
          ← Previous
        </span>
      )}
      <span className="muted">
        Page {page} of {pageCount} · {total} total
      </span>
      {hasNext ? (
        <Link href={`${basePath}${withQuery(searchParams, { offset: nextOffset })}`} className="btn btn--ghost">
          Next →
        </Link>
      ) : (
        <span className="btn btn--ghost" aria-disabled="true">
          Next →
        </span>
      )}
    </nav>
  );
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="empty">
      <div className="empty__title">{title}</div>
      {hint ? <div style={{ fontSize: 14 }}>{hint}</div> : null}
    </div>
  );
}

/**
 * Load failures must say what actually happened. A 401 means the session expired — telling the
 * user to "check the API is reachable" sends them debugging infrastructure that is working fine.
 */
export function LoadError({ status, entity }: { status?: number; entity: string }) {
  const expired = status === 401 || status === 403;
  return (
    <div className={`notice ${expired ? "notice--warn" : "notice--danger"}`}>
      <div className="notice__title">
        {expired ? "Your session expired" : `Couldn't load ${entity}`}
      </div>
      <div className="muted">
        {expired ? (
          <>
            Sign in again to continue — access tokens are short-lived by design.{" "}
            <Link href="/signin" style={{ color: "var(--accent)" }}>
              Sign in
            </Link>
          </>
        ) : (
          <>
            The Platform API didn&apos;t respond{status ? ` (HTTP ${status})` : ""}. Check that it
            is running.
          </>
        )}
      </div>
    </div>
  );
}
