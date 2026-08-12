#!/usr/bin/env bash
# Verify all relative Markdown links in the repo resolve to existing files.
# Referenced by CLAUDE.md §9 and the CI docs job. Exit non-zero if any link is broken.
set -uo pipefail

broken=0
# Prune heavy/vendored dirs; only our own Markdown is checked.
while IFS= read -r file; do
  dir=$(dirname "$file")
  # extract ](target.md) and ](target.md#anchor), strip anchors, skip http(s)
  grep -oE '\]\(([^)]+\.md)(#[^)]*)?\)' "$file" \
    | sed -E 's/\]\(//; s/\)$//; s/#.*$//' \
    | while read -r link; do
        case "$link" in http*) continue;; esac
        if [ ! -f "$dir/$link" ]; then
          echo "BROKEN: $file -> $link"
        fi
      done
done < <(find . \( -name .git -o -name node_modules -o -name .venv -o -name .next \
  -o -name dist -o -name build \) -prune -o -name '*.md' -print) | tee /tmp/dula-linkcheck.out

if [ -s /tmp/dula-linkcheck.out ]; then
  echo "Documentation link check FAILED."
  exit 1
fi
echo "Documentation link check passed."
