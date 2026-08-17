// Shared between the list, detail, and create pages, and the server actions — one place to
// keep in sync with dula_platform_api.models.Severity / IncidentStatus.
export const SEVERITIES = ["critical", "high", "medium", "low", "info"] as const;
export const STATUSES = ["open", "investigating", "contained", "resolved", "closed"] as const;
