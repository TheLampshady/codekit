#!/usr/bin/env bash
# Collects everything project-docs needs from git, so a run with no shell
# access (the codekit-docs Action) never has to call git itself.
#
#   collect_git.sh [--full] [<tmp>]
#
# Run it from the repo root. <tmp> defaults to ${TMPDIR:-/tmp}/codekit/<repo>.
# It pulls the current project docs into <tmp>/docs/ (Linear mode) or copies
# them from docs/project/ (repo mode), and writes the git input to <tmp>/git/:
#
#   repo.txt      name, root, head, base branch, base ref
#   mode.txt      mode (linear|repo), run (full|incremental), since, sync
#   log.txt       one line per commit to cover (empty on a full run)
#   messages.txt  the full messages of those commits
#   diffstat.txt  files changed by those commits
#   diff.patch    the patches of those commits
#   specs.txt     spec folders those commits added or changed
#   backfill/     merged spec folders, when the Decision Log doesn't exist yet,
#                 with backfill.txt listing "<folder> <date> <short rev>"
#
# Writes only under <tmp>. Never changes directory.
set -euo pipefail

full=0
tmp=""
for arg in "$@"; do
  case "$arg" in
    --full) full=1 ;;
    *) tmp="$arg" ;;
  esac
done

if [ -n "$(git rev-parse --show-prefix)" ]; then
  echo "collect_git.sh: run it from the repo root" >&2
  exit 1
fi
root=$(git rev-parse --show-toplevel)
name=$(basename "$root")
tmp=${tmp:-${TMPDIR:-/tmp}/codekit/$name}
out=$tmp/git
here=$(dirname "$(readlink -f "$0")")
project_docs=$here/../../linear-docs/scripts/project_docs.py

base=$(git config codekit.basebranch || true)
[ -n "$base" ] || base=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||' || true)
base=${base:-main}
ref=origin/$base
git rev-parse -q --verify "$ref" >/dev/null || ref=$base

mode=linear
[ "$(git config codekit.linear || true)" = "false" ] && mode=repo

rm -rf "$tmp/docs" "$out"
mkdir -p "$tmp/docs" "$out"

# Current docs. A doc that doesn't exist yet is fine.
if [ "$mode" = linear ]; then
  for title in "Product Map" "Glossary" "Decision Log"; do
    file=$(echo "$title" | tr 'A-Z ' 'a-z-').md
    python3 "$project_docs" pull --title "$title" --out "$tmp/docs/$file"
  done
else
  for file in product-map.md glossary.md decision-log.md; do
    [ -f "docs/project/$file" ] && cp "docs/project/$file" "$tmp/docs/$file"
  done
fi

# Full or incremental, from the map's sync line.
since=$(sed -n 's/.*Synced to commit \([0-9a-f]\{7,40\}\).*/\1/p' "$tmp/docs/product-map.md" 2>/dev/null | tail -1 || true)
run=incremental
if [ "$full" = 1 ] || [ -z "$since" ] || ! git merge-base --is-ancestor "$since" HEAD 2>/dev/null; then
  run=full
fi

if [ "$(git rev-parse --abbrev-ref HEAD)" = "$base" ]; then
  sync=$(git rev-parse HEAD)
else
  sync=$(git merge-base HEAD "$ref")
fi

{
  echo "name=$name"
  echo "root=$root"
  echo "head=$(git rev-parse HEAD)"
  echo "base=$base"
  echo "ref=$ref"
} > "$out/repo.txt"
{
  echo "mode=$mode"
  echo "run=$run"
  echo "since=$since"
  echo "sync=$sync"
} > "$out/mode.txt"

: > "$out/log.txt"; : > "$out/messages.txt"; : > "$out/diffstat.txt"
: > "$out/diff.patch"; : > "$out/specs.txt"

if [ "$run" = incremental ]; then
  own=$(git rev-list "$ref..HEAD" 2>/dev/null || true)
  for c in $(git rev-list --reverse "$since..HEAD"); do
    # Repo mode: a commit already on the base branch that changed docs/project/
    # was covered by its own update. This branch's own commits are always kept.
    if [ "$mode" = repo ] && ! grep -qx "$c" <<<"$own" \
       && [ -n "$(git diff-tree --no-commit-id --name-only -r "$c" -- docs/project)" ]; then
      continue
    fi
    git log -1 --oneline "$c" >> "$out/log.txt"
    git log -1 --format='commit %H%n%B%n---' "$c" >> "$out/messages.txt"
    git show --stat --format='commit %h %s' "$c" >> "$out/diffstat.txt"
    git show --format='commit %H' "$c" >> "$out/diff.patch"
    git show --name-only --format= "$c" -- specs openspec/changes/archive \
      | sed -n 's|^\(specs/[^/]*\)/.*|\1|p; s|^\(openspec/changes/archive/[^/]*\)/.*|\1|p' >> "$out/specs.txt"
  done
  sort -u -o "$out/specs.txt" "$out/specs.txt"
fi

# Backfill: spec folders already merged, read from git so unmerged work stays out.
if [ ! -f "$tmp/docs/decision-log.md" ]; then
  mkdir -p "$out/backfill"; : > "$out/backfill.txt"
  deleted=$(git log -1 --format=%H --diff-filter=D "$ref" -- specs || true)
  specs_rev=$ref
  [ -n "$deleted" ] && specs_rev=$deleted^
  for pair in "$specs_rev specs" "$ref openspec/changes/archive"; do
    rev=${pair%% *}; dir=${pair#* }
    for folder in $(git ls-tree -d --name-only "$rev" "$dir/" 2>/dev/null || true); do
      date=$(git log --reverse --format=%as "$rev" -- "$folder" | sed -n 1p)
      echo "$folder $date $(git rev-parse --short "$rev")" >> "$out/backfill.txt"
      for file in spec.md research.md plan.md design.md proposal.md; do
        if git cat-file -e "$rev:$folder/$file" 2>/dev/null; then
          mkdir -p "$out/backfill/$folder"
          git show "$rev:$folder/$file" > "$out/backfill/$folder/$file"
        fi
      done
    done
  done
fi

echo "collected $run run ($mode mode) into $tmp"
