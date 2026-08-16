import Link from "next/link";
import type { ReactNode } from "react";

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
            <Link href="/api/auth/signin" style={{ color: "var(--accent)" }}>
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
