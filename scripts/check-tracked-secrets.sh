#!/usr/bin/env bash
set -euo pipefail

forbidden_regex='(^|/)(\.env(\..*)?)$'
allowlist_regex='(^|/)\.env\.(example|sample|template|test)$'

tracked_files="$(git ls-files)"
violations="$(printf '%s\n' "$tracked_files" | grep -E "$forbidden_regex" | grep -Ev "$allowlist_regex" || true)"

if [[ -n "$violations" ]]; then
  echo "❌ Secret-bearing env files are tracked in git:" >&2
  printf '%s\n' "$violations" >&2
  echo "Remove from index with: git rm --cached <file>" >&2
  exit 1
fi

echo "✅ No tracked secret-bearing env files found."
