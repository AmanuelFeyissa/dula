"""Built-in connectors (docs/14-Plugins/ConnectorStandards.md).

First-party connectors delivered with the platform: a SIEM search (read), a threat-intel lookup
(read; offline fixture + an egress-gated live variant), and a ticketing create (consequential).
All are offline-capable so contract tests need no live calls; the live TI variant is inert in
air-gapped installs.
"""

from __future__ import annotations
