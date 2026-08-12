# Dula authorization policy (RBAC + tenant scope) — ADR-0009, docs/12-API/Authorization.md.
# Enforced at the service layer and at RAG retrieval. This is the Phase 01 starter policy;
# fine-grained ABAC and per-capability rules are added as endpoints land.
#
# Input contract:
#   {
#     "subject": { "roles": ["analyst"], "tenant_id": "..." },
#     "action":  "me.read",
#     "resource": { "tenant_id": "..." }   # optional; omitted for non-tenant resources
#   }
package dula.authz

import future.keywords.if
import future.keywords.in

default allow := false

# Role -> allowed actions (Phase 01 baseline; move to data bundle later).
role_actions := {
	"admin": {"*"},
	"analyst": {"me.read", "alerts.read", "incidents.read"},
}

# A subject's effective actions across all its roles.
subject_actions contains action if {
	some role in input.subject.roles
	action in role_actions[role]
}

# The subject is permitted the requested action.
action_permitted if "*" in subject_actions
action_permitted if input.action in subject_actions

# Tenant scope: if the resource is tenant-bound, it must match the subject's tenant.
tenant_ok if not input.resource
tenant_ok if not input.resource.tenant_id
tenant_ok if input.resource.tenant_id == input.subject.tenant_id

allow if {
	action_permitted
	tenant_ok
}
