# Tests for the Dula authorization policy. Run with: opa test deploy/opa/policy
package dula.authz

import future.keywords.if

test_analyst_can_read_me if {
	allow with input as {"subject": {"roles": ["analyst"], "tenant_id": "t1"}, "action": "me.read"}
}

test_analyst_cannot_write if {
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
