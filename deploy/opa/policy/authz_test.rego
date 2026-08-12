# Tests for the Dula authorization policy. Run with: opa test deploy/opa/policy
package dula.authz

import rego.v1

test_analyst_can_read_me if {
	allow with input as {"subject": {"roles": ["analyst"], "tenant_id": "t1"}, "action": "me.read"}
}

test_analyst_can_create_alert if {
	allow with input as {
		"subject": {"roles": ["analyst"], "tenant_id": "t1"},
		"action": "alerts.create",
		"resource": {"tenant_id": "t1"},
	}
}

test_analyst_cannot_delete_alert if {
	not allow with input as {
		"subject": {"roles": ["analyst"], "tenant_id": "t1"},
		"action": "alerts.delete",
		"resource": {"tenant_id": "t1"},
	}
}

test_engineer_can_manage_assets if {
	allow with input as {
		"subject": {"roles": ["engineer"], "tenant_id": "t1"},
		"action": "assets.delete",
		"resource": {"tenant_id": "t1"},
	}
}

test_hunter_cannot_manage_assets if {
	not allow with input as {
		"subject": {"roles": ["hunter"], "tenant_id": "t1"},
		"action": "assets.create",
		"resource": {"tenant_id": "t1"},
	}
}

test_responder_can_close_incident if {
	allow with input as {
		"subject": {"roles": ["responder"], "tenant_id": "t1"},
		"action": "incidents.delete",
		"resource": {"tenant_id": "t1"},
	}
}

test_unknown_action_denied if {
	not allow with input as {"subject": {"roles": ["analyst"], "tenant_id": "t1"}, "action": "alerts.write"}
}

test_admin_wildcard if {
	allow with input as {"subject": {"roles": ["admin"], "tenant_id": "t1"}, "action": "anything.goes"}
}

test_cross_tenant_denied if {
	not allow with input as {
		"subject": {"roles": ["analyst"], "tenant_id": "t1"},
		"action": "alerts.read",
		"resource": {"tenant_id": "t2"},
	}
}

test_same_tenant_allowed if {
	allow with input as {
		"subject": {"roles": ["analyst"], "tenant_id": "t1"},
		"action": "alerts.read",
		"resource": {"tenant_id": "t1"},
	}
}

test_no_roles_denied if {
	not allow with input as {"subject": {"roles": [], "tenant_id": "t1"}, "action": "alerts.read"}
}

test_analyst_can_ask_ai if {
	allow with input as {
		"subject": {"roles": ["analyst"], "tenant_id": "t1"},
		"action": "ai.ask",
		"resource": {"tenant_id": "t1"},
	}
}

test_hunter_can_triage if {
	allow with input as {
		"subject": {"roles": ["hunter"], "tenant_id": "t1"},
		"action": "ai.triage",
		"resource": {"tenant_id": "t1"},
	}
}

test_analyst_can_ingest_knowledge if {
	allow with input as {
		"subject": {"roles": ["analyst"], "tenant_id": "t1"},
		"action": "knowledge.ingest",
		"resource": {"tenant_id": "t1"},
	}
}

test_analyst_cannot_purge_knowledge if {
	not allow with input as {
		"subject": {"roles": ["analyst"], "tenant_id": "t1"},
		"action": "knowledge.purge",
		"resource": {"tenant_id": "t1"},
	}
}

test_admin_can_purge_knowledge if {
	allow with input as {
		"subject": {"roles": ["admin"], "tenant_id": "t1"},
		"action": "knowledge.purge",
		"resource": {"tenant_id": "t1"},
	}
}
