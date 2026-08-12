# ADR-0001: Product & Ecosystem Naming

- Status: Accepted
- Date: 2026-08-11
- Deciders: Product owner (user), Founding Engineering
- Related: [../02-Vision/Vision.md](../02-Vision/Vision.md)

## Context
The bootstrap used placeholder names ("Aegis"/"SecLLM"). A permanent, meaningful name was
needed before the documentation stabilized.

## Options Considered
1. Keep placeholders — rejected (not meaningful; confusing).
2. Generic security terms — rejected (crowded, trademark risk).
3. **Dula / Dula AI** — an Oromo-language name with defensive meaning.

## Decision
- **Dula** = the Cybersecurity AI Platform (Product 1) and the overall ecosystem name.
- **Dula AI** = the cybersecurity-specialized LLM (Product 2).
- **Etymology:** Oromo *Duulaa* = a warrior/knight; *Abbaa Duulaa* = the traditional war
  leader / army commander / defense minister in the Gadaa system. The name expresses the
  product's defensive-guardian mission.
- Model artifacts use the `dula-` prefix (e.g. `dula-<base>-<task>-<method>-vX.Y`).

## Consequences
- All documentation updated from Aegis/SecLLM to Dula/Dula AI (search-and-replace + file
  renames `DulaAIStrategy.md`, `Phase04-DulaAI.md`).
- **Trademark clearance** for commercial use remains a business task (out of engineering
  scope).

## Compliance / Verification
- CI/docs check: no occurrences of "Aegis" or "SecLLM" remain (verified at decision time).
