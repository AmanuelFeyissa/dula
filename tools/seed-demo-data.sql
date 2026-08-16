-- Demo seed data for local development (see RUNNING.md).
--
-- Gives the UI something realistic to show: two tenants (proving isolation), assets,
-- alerts, and incidents that hang together as a plausible SOC picture. Values match the
-- app-layer enums in apps/platform-api/src/dula_platform_api/models.py.
--
-- Idempotent: safe to re-run (fixed UUIDs + ON CONFLICT DO NOTHING).
-- Usage: docker exec -i dula-dev-postgres-1 psql -U dula -d dula < tools/seed-demo-data.sql

BEGIN;

-- Tenants ------------------------------------------------------------------------------
INSERT INTO tenants (id, name) VALUES
  ('11111111-1111-1111-1111-111111111111', 'Acme Corp'),
  ('22222222-2222-2222-2222-222222222222', 'Globex (second tenant)')
ON CONFLICT (id) DO NOTHING;

-- Assets -------------------------------------------------------------------------------
INSERT INTO assets (id, tenant_id, name, asset_type, identifier, criticality, description) VALUES
  ('a0000000-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111', 'HOST-7',        'host',           'host-7.acme.internal',        'critical', 'Finance workstation; handles payment runs.'),
  ('a0000000-0000-0000-0000-000000000002', '11111111-1111-1111-1111-111111111111', 'HOST-3',        'host',           'host-3.acme.internal',        'medium',   'Engineering laptop.'),
  ('a0000000-0000-0000-0000-000000000003', '11111111-1111-1111-1111-111111111111', 'svc-billing',   'account',        'svc-billing@acme.internal',   'high',     'Service account for the billing pipeline.'),
  ('a0000000-0000-0000-0000-000000000004', '11111111-1111-1111-1111-111111111111', 'prod-s3-audit', 'cloud_resource', 'arn:aws:s3:::acme-audit-logs', 'high',     'Immutable audit-log bucket.'),
  ('a0000000-0000-0000-0000-000000000005', '11111111-1111-1111-1111-111111111111', 'payments-api',  'k8s_resource',   'prod/deploy/payments-api',    'critical', 'Payment processing service.'),
  -- Second tenant (must never be visible to tenant 1)
  ('a0000000-0000-0000-0000-000000000091', '22222222-2222-2222-2222-222222222222', 'GLOBEX-DC1',    'host',           'dc1.globex.internal',         'critical', 'Globex domain controller.')
ON CONFLICT (id) DO NOTHING;

-- Incidents ----------------------------------------------------------------------------
INSERT INTO incidents (id, tenant_id, title, description, severity, status, assignee_subject) VALUES
  ('c0000000-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111',
   'Suspected C2 beaconing from HOST-7',
   'Recurring 60s outbound connections to evil.example.com from a finance workstation. Under investigation.',
   'critical', 'investigating', 'maya'),
  ('c0000000-0000-0000-0000-000000000002', '11111111-1111-1111-1111-111111111111',
   'Credential stuffing against the VPN portal',
   'Spike of failed logins from a single ASN across 40+ accounts. Rate limiting applied.',
   'high', 'contained', 'raj'),
  ('c0000000-0000-0000-0000-000000000003', '11111111-1111-1111-1111-111111111111',
   'Phishing campaign targeting finance',
   'Invoice-themed lure with a credential-harvesting link. Mailbox rules deployed.',
   'medium', 'resolved', 'maya'),
  ('c0000000-0000-0000-0000-000000000091', '22222222-2222-2222-2222-222222222222',
   'Globex — ransomware precursor activity',
   'Shadow copy deletion observed on the domain controller.',
   'critical', 'open', 'tariq')
ON CONFLICT (id) DO NOTHING;

-- Alerts -------------------------------------------------------------------------------
INSERT INTO alerts (id, tenant_id, title, description, severity, status, source, asset_id, incident_id) VALUES
  ('b0000000-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111',
   'Suspicious outbound beacon', 'HOST-7 contacted evil.example.com on a fixed 60s interval (37 times in 1h).',
   'critical', 'in_progress', 'Suricata', 'a0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001'),
  ('b0000000-0000-0000-0000-000000000002', '11111111-1111-1111-1111-111111111111',
   'Impossible travel sign-in', 'svc-billing authenticated from Lagos 8 minutes after a Frankfurt session.',
   'high', 'triaged', 'Entra ID', 'a0000000-0000-0000-0000-000000000003', 'c0000000-0000-0000-0000-000000000002'),
  ('b0000000-0000-0000-0000-000000000003', '11111111-1111-1111-1111-111111111111',
   'Malware quarantine failed', 'EDR could not quarantine a mimikatz-like binary on HOST-3.',
   'high', 'new', 'CrowdStrike', 'a0000000-0000-0000-0000-000000000002', NULL),
  ('b0000000-0000-0000-0000-000000000004', '11111111-1111-1111-1111-111111111111',
   'Audit log bucket policy changed', 'Public-read grant added to acme-audit-logs, then reverted after 4 minutes.',
   'critical', 'new', 'CloudTrail', 'a0000000-0000-0000-0000-000000000004', NULL),
  ('b0000000-0000-0000-0000-000000000005', '11111111-1111-1111-1111-111111111111',
   'Anomalous pod exec in production', 'kubectl exec into payments-api by a non-oncall identity.',
   'medium', 'new', 'Falco', 'a0000000-0000-0000-0000-000000000005', NULL),
  ('b0000000-0000-0000-0000-000000000006', '11111111-1111-1111-1111-111111111111',
   'Brute-force against VPN portal', '312 failed authentications from 41 accounts within 6 minutes.',
   'high', 'closed', 'VPN Gateway', NULL, 'c0000000-0000-0000-0000-000000000002'),
  ('b0000000-0000-0000-0000-000000000007', '11111111-1111-1111-1111-111111111111',
   'Phishing link clicked', 'User opened hxxp://acme-invoice[.]example/login from an email lure.',
   'medium', 'closed', 'Proofpoint', NULL, 'c0000000-0000-0000-0000-000000000003'),
  ('b0000000-0000-0000-0000-000000000008', '11111111-1111-1111-1111-111111111111',
   'Scheduled task created on HOST-7', 'Persistence via schtasks pointing at a temp-directory payload.',
   'high', 'in_progress', 'Sysmon', 'a0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001'),
  ('b0000000-0000-0000-0000-000000000009', '11111111-1111-1111-1111-111111111111',
   'Legacy TLS negotiated', 'TLS 1.0 handshake observed to a partner endpoint.',
   'low', 'false_positive', 'Zeek', NULL, NULL),
  ('b0000000-0000-0000-0000-000000000010', '11111111-1111-1111-1111-111111111111',
   'New admin account created', 'Account "svc_helpdesk2" added to Domain Admins outside a change window.',
   'critical', 'new', 'Windows Security', NULL, NULL),
  -- Second tenant (isolation check)
  ('b0000000-0000-0000-0000-000000000091', '22222222-2222-2222-2222-222222222222',
   'Shadow copy deletion', 'vssadmin delete shadows /all executed on GLOBEX-DC1.',
   'critical', 'new', 'Sysmon', 'a0000000-0000-0000-0000-000000000091', 'c0000000-0000-0000-0000-000000000091')
ON CONFLICT (id) DO NOTHING;

COMMIT;

SELECT 'tenants' AS entity, count(*) FROM tenants
UNION ALL SELECT 'assets', count(*) FROM assets
UNION ALL SELECT 'alerts', count(*) FROM alerts
UNION ALL SELECT 'incidents', count(*) FROM incidents;
