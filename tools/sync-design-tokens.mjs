#!/usr/bin/env node
// Copy the Dula design tokens into the Keycloak login theme.
//
// The sign-in page is served by Keycloak, not by Next.js, so it cannot import the app's CSS.
// Rather than maintain two palettes that silently drift apart, the theme's token file is
// generated from apps/web/app/design-tokens.css and checked in.
//
//   node tools/sync-design-tokens.mjs            # regenerate
//   node tools/sync-design-tokens.mjs --check    # verify (CI); exit 1 if stale
//
// No dependencies and no network: this has to work in an air-gapped checkout (CLAUDE.md §7).

import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const SOURCE = join(repoRoot, "apps", "web", "app", "design-tokens.css");
const TARGET = join(
  repoRoot,
  "deploy",
  "docker",
  "keycloak",
  "themes",
  "dula",
  "login",
  "resources",
  "css",
  "tokens.css",
);

const BANNER = `/* GENERATED FILE — DO NOT EDIT.
 *
 * Source: apps/web/app/design-tokens.css
 * Regenerate: node tools/sync-design-tokens.mjs
 *
 * Edits here will be overwritten and will fail the CI drift check.
 */
`;

function build() {
  // Strip the source's leading block comment; the banner above replaces it.
  const body = readFileSync(SOURCE, "utf8").replace(/^\/\*[\s\S]*?\*\/\s*/, "");
  return `${BANNER}\n${body}`;
}

const expected = build();
const check = process.argv.includes("--check");

if (check) {
  let actual = "";
  try {
    actual = readFileSync(TARGET, "utf8");
  } catch {
    console.error(`Missing ${TARGET}. Run: node tools/sync-design-tokens.mjs`);
    process.exit(1);
  }
  if (actual !== expected) {
    console.error(
      "Keycloak theme tokens are out of sync with apps/web/app/design-tokens.css.\n" +
        "Run: node tools/sync-design-tokens.mjs",
    );
    process.exit(1);
  }
  console.log("Design tokens are in sync.");
} else {
  mkdirSync(dirname(TARGET), { recursive: true });
  writeFileSync(TARGET, expected);
  console.log(`Wrote ${TARGET}`);
}
