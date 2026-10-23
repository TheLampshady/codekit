#!/usr/bin/env python3
"""
Read and write a Linear project's documents, so long docs (the product map,
the glossary) move between disk and Linear without passing through the model.

    python3 project_docs.py pull --title "Product Map" --out FILE [--project ID]
    python3 project_docs.py push FILE [FILE ...] [--project ID] [--dry-run]

- pull writes the document with that title to FILE. If the project has no
  such document, it says so, writes nothing, and exits 0.
- push uploads each FILE as one document, titled with the file's first
  "# " heading (else the file name), creating it or overwriting the one with
  that title. A document whose words haven't changed is left alone.
- The project is --project, else `git config codekit.linear-project`, else
  that key in the committed .config/.gitconfig.
- The key is LINEAR_API_KEY from the environment. The key is never printed.

Standard library only, so it runs with any Python 3.10+.
"""

import argparse
import re
import sys
from pathlib import Path

from linear_docs import (
    MISSING_KEY,
    api_key,
    codekit_config,
    graphql,
    project_root,
    same_words,
)

HEADING = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)

PROJECT_QUERY = """
query Project($id: String!) {
  project(id: $id) {
    id name url
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


def title_of(path: Path, content: str) -> str:
    match = HEADING.search(content)
    return match.group(1) if match else path.stem


def load_project(key: str, project_id: str) -> dict:
    project = graphql(key, PROJECT_QUERY, {"id": project_id})["project"]
    if not project:
        raise SystemExit(f"No Linear project {project_id}.")
    return project


def pull(key: str, project: dict, title: str, out: Path) -> int:
    for doc in project["documents"]["nodes"]:
        if doc["title"] == title:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(doc.get("content") or "", encoding="utf-8")
            print(f"pulled   {title} -> {out}")
            return 0
    print(f"missing  {title} (not in {project['name']})")
    return 0


def push(key: str, project: dict, files: list[Path], dry_run: bool) -> int:
    by_title = {d["title"]: d for d in project["documents"]["nodes"]}
    print(f"{project['name']} {project['url']}")
    plan = []
    for path in files:
        content = path.read_text(encoding="utf-8")
        title = title_of(path, content)
        remote = by_title.get(title)
        if remote is None:
            kind = "create"
        elif same_words(content, remote.get("content") or ""):
            kind = "unchanged"
        else:
            kind = "update"
        plan.append((kind, title, remote["id"] if remote else None, content))
        print(f"  {kind:<9} {title}")
    if dry_run:
        print("Dry run: nothing written.")
        return 0
    for kind, title, doc_id, content in plan:
        if kind == "create":
            graphql(
                key,
                CREATE,
                {"input": {"projectId": project["id"], "title": title, "content": content}},
            )
        elif kind == "update":
            graphql(key, UPDATE, {"id": doc_id, "input": {"content": content}})
    changed = sum(kind != "unchanged" for kind, *_ in plan)
    print(f"Done: {changed} change(s).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("command", choices=("pull", "push"))
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument("--project")
    parser.add_argument("--title")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    root = project_root()
    project_id = args.project or codekit_config(root, "linear-project")
    if not project_id:
        print(
            "No project: pass --project or set `git config codekit.linear-project`.",
            file=sys.stderr,
        )
        return 1
    key = api_key()
    if not key:
        print(MISSING_KEY, file=sys.stderr)
        return 1
    project = load_project(key, project_id)

    if args.command == "pull":
        if not args.title or not args.out:
            print("pull needs --title and --out.", file=sys.stderr)
            return 1
        return pull(key, project, args.title, args.out)
    missing = [p for p in args.files if not p.is_file()]
    if not args.files or missing:
        print(f"push needs existing files; missing: {missing or 'none given'}", file=sys.stderr)
        return 1
    return push(key, project, args.files, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
