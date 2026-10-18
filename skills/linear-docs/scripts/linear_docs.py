#!/usr/bin/env python3
"""
Keep a spec folder's decision-bearing files on its Linear issue as documents,
one per file, adding new ones and overwriting the ones with the same title.
The issue is the spec's copy of record; the folder itself isn't committed.

    python3 linear_docs.py [FOLDER] [--issue ENG-123] [--team ENG]
        [--dry-run] [--prune] [--yes]
    python3 linear_docs.py --pull FOLDER --issue ENG-123 [--yes]
    python3 linear_docs.py --check

- Run from inside the project; its root is the enclosing git repo.
- FOLDER defaults to the SpecKit feature in .specify/feature.json, else the
  OpenSpec change or specs/ folder named after the branch's Linear issue.
- The issue defaults to a "**Linear:** ENG-123" line in spec.md, ticket.md, or
  proposal.md, else the identifier in the folder name, else in the branch.
- The key is LINEAR_API_KEY from the environment. The key is never printed.
- With --team, or `git config codekit.linear-team`, issues on other teams are
  refused.
- Only spec.md, plan.md, research.md (SpecKit, manual) and proposal.md,
  design.md (OpenSpec) are uploaded: the files that carry what was decided and
  why. Tasks, contracts, data models and the rest are build-time only.
- --prune also deletes issue documents with no local file (asks unless --yes).
- --pull writes the issue's documents into FOLDER, e.g. to resume work on
  another machine or to extract decisions after merge. Existing files are kept
  unless --yes.
- --check only verifies the key works and prints whose it is; nothing is read
  from or written to any issue.

Standard library only, so it runs with any Python 3.10+.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request

API_URL = "https://api.linear.app/graphql"

# The files worth keeping after the build, in reading order (SpecKit and
# OpenSpec names mixed; a folder only has one set). Everything else in a spec
# folder is superseded by the code once it ships.
DOC_ORDER = (
    "spec.md",
    "proposal.md",
    "plan.md",
    "design.md",
    "research.md",
)
SPEC_FILES = ("spec.md", "ticket.md", "proposal.md")

ISSUE_ID = r"[A-Za-z][A-Za-z0-9]+-\d+"
LINEAR_LINE = re.compile(
    r"\*\*Linear:?\*\*:?\s*\[?(" + ISSUE_ID + r")", re.IGNORECASE
)
ID_IN_NAME = re.compile(r"(?<![A-Za-z0-9])(" + ISSUE_ID + r")")
URL = re.compile(r"https?://[^\s)>\]]+")
WORD = re.compile(r"[^\W_]+")


@dataclass(frozen=True)
class LocalDoc:
    title: str
    content: str


@dataclass(frozen=True)
class Action:
    kind: str  # create | update | unchanged | delete
    title: str
    doc_id: str | None = None
    content: str = ""


def git(root: Path, *args: str) -> str:
    try:
        out = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    return out.stdout.strip()


def project_root() -> Path:
    top = git(Path.cwd(), "rev-parse", "--show-toplevel")
    return Path(top) if top else Path.cwd()


def issue_in(name: str) -> str | None:
    match = ID_IN_NAME.search(name)
    return match.group(1).upper() if match else None


def collect_documents(folder: Path) -> list[LocalDoc]:
    """One document per decision-bearing file the folder has, in reading order."""
    return [
        LocalDoc(name, (folder / name).read_text(encoding="utf-8"))
        for name in DOC_ORDER
        if (folder / name).is_file()
    ]


def pull_documents(
    issue: dict[str, Any], folder: Path, root: Path, overwrite: bool
) -> int:
    """Write the issue's spec documents into folder, keeping existing files."""
    folder.mkdir(parents=True, exist_ok=True)
    wanted = set(DOC_ORDER)
    print(f"{issue['identifier']} {issue['url']}  -> {display(folder, root)}")
    found = 0
    for doc in issue["documents"]["nodes"]:
        if doc["title"] not in wanted:
            continue
        found += 1
        path = folder / doc["title"]
        if path.exists() and not overwrite:
            print(f"  kept      {doc['title']} (exists locally)")
            continue
        path.write_text(doc.get("content") or "", encoding="utf-8")
        print(f"  pulled    {doc['title']}")
    if not found:
        print("  none      (the issue has no spec documents)")
    return 0


def issue_from_folder(folder: Path) -> str | None:
    for name in SPEC_FILES:
        path = folder / name
        if path.exists():
            match = LINEAR_LINE.search(path.read_text(encoding="utf-8"))
            if match:
                return match.group(1).upper()
    return issue_in(folder.name)


def default_folder(root: Path, branch_issue: str | None) -> Path | None:
    """SpecKit's active feature, else a folder named after the branch's issue."""
    feature = root / ".specify" / "feature.json"
    if feature.exists():
        folder = json.loads(feature.read_text(encoding="utf-8")).get(
            "feature_directory"
        )
        if folder:
            return root / folder
    if branch_issue:
        for parent in (root / "openspec" / "changes", root / "specs"):
            for candidate in sorted(parent.glob("*")):
                if candidate.is_dir() and issue_in(candidate.name) == branch_issue:
                    return candidate
    return None


def same_words(local: str, remote: str) -> bool:
    """
    Whether two texts say the same thing. Linear rewrites markdown on save
    (bullets, link brackets, issue ids turned into links), so only the words
    are compared, with URLs left out. A formatting-only edit does not count.
    """

    def words(text: str) -> list[str]:
        return WORD.findall(URL.sub(" ", text))

    return words(local) == words(remote)


def plan_sync(
    local: list[LocalDoc], remote: list[dict[str, Any]], prune: bool
) -> list[Action]:
    """Match by title: create, update, or leave unchanged; with prune, delete the rest."""
    by_title: dict[str, list[dict[str, Any]]] = {}
    for doc in remote:
        by_title.setdefault(doc["title"], []).append(doc)
    actions: list[Action] = []
    for doc in local:
        matches = by_title.pop(doc.title, [])
        if not matches:
            actions.append(Action("create", doc.title, content=doc.content))
            continue
        first, *extra = matches
        same = same_words(doc.content, first.get("content") or "")
        actions.append(
            Action(
                "unchanged" if same else "update", doc.title, first["id"], doc.content
            )
        )
        if prune:
            actions += [Action("delete", d["title"], d["id"]) for d in extra]
    if prune:
        for docs in by_title.values():
            actions += [Action("delete", d["title"], d["id"]) for d in docs]
    return actions


def api_key() -> str:
    """LINEAR_API_KEY from the environment."""
    return os.environ.get("LINEAR_API_KEY", "").strip()


def graphql(key: str, query: str, variables: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = request.Request(
        API_URL,
        data=body,
        headers={"Content-Type": "application/json", "Authorization": key},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Linear returned {exc.code}: {detail}") from exc
    if payload.get("errors"):
        raise SystemExit(
            "Linear error: "
            + "; ".join(e.get("message", "") for e in payload["errors"])
        )
    return payload["data"]


VIEWER_QUERY = """
query Viewer {
  viewer { name email }
  organization { name urlKey }
}"""
ISSUE_QUERY = """
query Issue($id: String!) {
  issue(id: $id) {
    id identifier url team { key }
    documents(first: 100) { nodes { id title content } }
  }
}"""
CREATE = """
mutation Create($input: DocumentCreateInput!) {
  documentCreate(input: $input) { success }
}"""
UPDATE = """
mutation Update($id: String!, $input: DocumentUpdateInput!) {
  documentUpdate(id: $id, input: $input) { success }
}"""
DELETE = """
mutation Delete($id: String!) {
  documentDelete(id: $id) { success }
}"""


def display(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


MISSING_KEY = (
    "LINEAR_API_KEY is not set. Export it in your shell profile "
    "(Linear: Settings > Security & access > Personal API keys)."
)


def check_key() -> int:
    """Verify LINEAR_API_KEY against the API without touching any issue."""
    key = api_key()
    if not key:
        print(MISSING_KEY, file=sys.stderr)
        return 1
    data = graphql(key, VIEWER_QUERY, {})
    viewer, org = data["viewer"], data["organization"]
    print(
        f"LINEAR_API_KEY ok: {viewer['name']} <{viewer['email']}> "
        f"in {org['name']} (linear.app/{org['urlKey']})"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("folder", nargs="?", type=Path)
    parser.add_argument("--issue")
    parser.add_argument("--team")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--prune", action="store_true")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--pull", action="store_true")
    args = parser.parse_args(argv)

    if args.check:
        return check_key()

    root = project_root()
    if args.pull:
        if not args.folder or not args.issue:
            print("--pull needs a FOLDER and --issue ENG-123.", file=sys.stderr)
            return 1
        key = api_key()
        if not key:
            print(MISSING_KEY, file=sys.stderr)
            return 1
        issue = graphql(key, ISSUE_QUERY, {"id": args.issue.upper()})["issue"]
        return pull_documents(issue, args.folder.resolve(), root, args.yes)

    branch_issue = issue_in(git(root, "branch", "--show-current"))
    folder = args.folder or default_folder(root, branch_issue)
    folder = folder.resolve() if folder else None
    if folder is None or not folder.is_dir():
        print(
            f"No spec folder at {folder}. Pass one, e.g. specs/001-name or "
            "openspec/changes/eng-123-name.",
            file=sys.stderr,
        )
        return 1
    identifier = (args.issue or issue_from_folder(folder) or branch_issue or "").upper()
    if not identifier:
        print(
            "No issue: pass --issue ENG-123 or add '**Linear:** ENG-123' to spec.md.",
            file=sys.stderr,
        )
        return 1
    key = api_key()
    if not key:
        print(MISSING_KEY, file=sys.stderr)
        return 1

    issue = graphql(key, ISSUE_QUERY, {"id": identifier})["issue"]
    team = (args.team or git(root, "config", "codekit.linear-team")).upper()
    issue_team = ((issue.get("team") or {}).get("key") or "").upper()
    if team and issue_team != team:
        print(f"{identifier} is on team {issue_team}, not {team}; nothing changed.")
        return 1

    docs = collect_documents(folder)
    if not docs:
        print(f"No markdown files in {display(folder, root)}; nothing to sync.")
        return 1
    actions = plan_sync(docs, issue["documents"]["nodes"], args.prune)
    print(f"{issue['identifier']} {issue['url']}  <- {display(folder, root)}")
    for act in actions:
        print(f"  {act.kind:<9} {act.title}")
    if args.dry_run:
        print("Dry run: nothing written.")
        return 0

    deletes = [a for a in actions if a.kind == "delete"]
    if deletes and not args.yes:
        answer = input(f"Delete {len(deletes)} document(s) from Linear? [y/N] ")
        if answer.strip().lower() not in ("y", "yes"):
            print("Stopped: nothing written.")
            return 1

    for act in actions:
        if act.kind == "create":
            graphql(
                key,
                CREATE,
                {
                    "input": {
                        "issueId": issue["id"],
                        "title": act.title,
                        "content": act.content,
                    }
                },
            )
        elif act.kind == "update":
            graphql(key, UPDATE, {"id": act.doc_id, "input": {"content": act.content}})
        elif act.kind == "delete":
            graphql(key, DELETE, {"id": act.doc_id})
    changed = sum(a.kind != "unchanged" for a in actions)
    print(f"Done: {changed} change(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
