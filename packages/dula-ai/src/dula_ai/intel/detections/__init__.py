"""Detection authoring (UC-04 — draft/validate Sigma & YARA, ATT&CK coverage).

Rules are authored **deterministically** from structured input and always pass their own
validator before being returned, so generated detections are syntactically valid and reviewable
(Phase 05 acceptance criterion). A model draft may be validated by the same functions — invalid
rules are rejected, never emitted. Detection authoring is defensive-only.
"""

from __future__ import annotations
