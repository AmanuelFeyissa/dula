// Shared between the list, detail, and create pages, and the server actions — one place to
// keep in sync with dula_platform_api.models.Severity / AlertStatus.
export const SEVERITIES = ["critical", "high", "medium", "low", "info"] as const;
export const STATUSES = ["new", "triaged", "in_progress", "closed", "false_positive"] as const;
