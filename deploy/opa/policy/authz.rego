# Dula authorization policy (RBAC + tenant scope) — ADR-0009, docs/12-API/Authorization.md.
# Enforced at the service layer and (later) at RAG retrieval. Phase 02 covers the core
# domain: assets, alerts, incidents. Fine-grained ABAC (owner, data classification) is
# layered on as those attributes land.
#
# Input contract:
#   {
#     "subject": { "roles": ["analyst"], "tenant_id": "..." },
#     "action":  "alerts.create",
#     "resource": { "tenant_id": "..." }   # optional; omitted for non-tenant resources
#   }
package dula.authz

import rego.v1

default allow := false

# Operational personas (TargetUsers.md). Any of these may perform coarse reads.
operational_roles := {"analyst", "hunter", "responder", "engineer", "admin"}

# Coarse read set shared by every operational persona.
read_actions := {"me.read", "assets.read", "alerts.read", "incidents.read"}

# AI actions (grounded Q&A / triage) — available to every operational persona (Phase 03).
# Cyber-intelligence actions (Phase 05): CTI extraction, vulnerability analysis, and detection
# authoring — grounded/deterministic, defensive-only, available to every operational persona.
# Agent actions (Phase 06): running an investigation agent, reading its trace, hitting the
# approval endpoint, and the READ-only agent tools. Approval only *takes effect* if the approver
# is also authorized for the specific consequential tool (re-checked by the agent runtime), so
# `agents.approve` here just admits the request. Consequential tools are role-gated below.
ai_actions := {
	"ai.ask", "ai.triage", "ai.cti", "ai.vuln", "ai.detect",
	"agents.run", "agents.read", "agents.approve",
	"tool.search_logs", "tool.enrich_indicator", "tool.list_alerts",
}

# Role -> additional (write) actions. `admin` is unrestricted; others follow least privilege.
# Consequential agent tools: create_ticket for responders/analysts/hunters/engineers; the
# higher-impact isolate_host containment for responders only (admin via `*`).
role_actions := {
	"admin": {"*"},
	"analyst": {"alerts.create", "alerts.update", "incidents.create", "knowledge.ingest", "tool.create_ticket"},
	"hunter": {"alerts.create", "alerts.update", "knowledge.ingest", "tool.create_ticket"},
	"responder": {
		"incidents.create",
		"incidents.update",
		"incidents.delete",
		"alerts.update",
		"tool.create_ticket",
		"tool.isolate_host",
	},
	"engineer": {
		"assets.create",
		"assets.update",
		"assets.delete",
		"alerts.create",
		"alerts.update",
		"alerts.delete",
		"knowledge.ingest",
		"tool.create_ticket",
	},
}

# A subject's effective write actions across all of its roles.
subject_actions contains action if {
	some role in input.subject.roles
	some action in role_actions[role]
}

# The subject holds at least one operational role.
has_operational_role if {
	some role in input.subject.roles
	role in operational_roles
}

# The subject is permitted the requested action.
action_permitted if "*" in subject_actions

action_permitted if input.action in subject_actions

action_permitted if {
	input.action in read_actions
	has_operational_role
}

action_permitted if {
	input.action in ai_actions
	has_operational_role
}

# Tenant scope: if the resource is tenant-bound, it must match the subject's tenant.
tenant_ok if not input.resource

tenant_ok if not input.resource.tenant_id

tenant_ok if input.resource.tenant_id == input.subject.tenant_id

allow if {
	action_permitted
	tenant_ok
}
