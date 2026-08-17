// Mirrors `role_actions` in deploy/opa/policy/authz.rego — hand-kept in sync. This is UI-only:
// it decides which controls to *offer*, never which requests to *allow*. Every write still goes
// through the Platform API, which re-evaluates the same policy in OPA and is authoritative
// (ADR-0009). Drift here can only make the UI too conservative (a control stays hidden that OPA
// would in fact allow) — it can never grant something the backend would refuse, so an out-of-date
// map is a UX bug, not a security bug.
const ROLE_ACTIONS: Readonly<Record<string, ReadonlySet<string> | "*">> = {
  admin: "*",
  analyst: new Set(["alerts.create", "alerts.update", "incidents.create"]),
  hunter: new Set(["alerts.create", "alerts.update"]),
  responder: new Set(["incidents.create", "incidents.update", "alerts.update"]),
  engineer: new Set(["assets.create", "assets.update", "alerts.create", "alerts.update"]),
};

export function can(roles: readonly string[], action: string): boolean {
  return roles.some((role) => {
    const actions = ROLE_ACTIONS[role];
    return actions === "*" || (actions?.has(action) ?? false);
  });
}
