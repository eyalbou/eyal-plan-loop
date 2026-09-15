#!/usr/bin/env bash
# Push this skill from local to both GitHub copies. Then resync in Willow.
set -euo pipefail

SRC="${EYAL_PLAN_LOOP_SRC:-$HOME/.cursor/skills/eyal-plan-loop}"
if [[ ! -f "$SRC/SKILL.md" ]]; then
  echo "Missing SKILL.md at $SRC" >&2
  exit 1
fi

ship_to() {
  local repo="$1"
  local dest_rel="$2"
  local tmp
  tmp="$(mktemp -d)"
  git clone --depth 1 "git@github.com:${repo}.git" "$tmp/repo"
  mkdir -p "$tmp/repo/$dest_rel"
  rsync -a --delete --exclude '.git' "$SRC/" "$tmp/repo/$dest_rel/"
  (
    cd "$tmp/repo"
    git add -A
    if git diff --cached --quiet; then
      echo "No changes: $repo"
      return 0
    fi
    git commit -m "Sync eyal-plan-loop from local skill."
    git push
    echo "Pushed: $repo"
  )
}

ship_to "eyalbou/eyal-plan-loop" "skills/eyal-plan-loop"
ship_to "eyalbou/eyal-personal-skills" "skills/eyal-plan-loop"
echo "Done. Resync From GitHub in Willow."
