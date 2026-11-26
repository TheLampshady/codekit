#!/usr/bin/env python3
"""
Keep specs and project docs in the code host's wiki. A GitLab wiki is a git
repo next to the code (the origin remote with .wiki.git in place of .git), so
this works through plain git on any GitLab host, gitlab.com or self-managed,
by name or IP address, with the login that already reaches the code.

    python3 wiki_docs.py check
    python3 wiki_docs.py push FOLDER [--name NAME] [--prune] [--yes] [--dry-run]
    python3 wiki_docs.py pull FOLDER --issue REF [--yes]
    python3 wiki_docs.py pull-doc --title TITLE --out FILE
    python3 wiki_docs.py push-docs FILE [FILE ...] [--dry-run]

- Run from inside the project; the wiki is found from `git remote get-url origin`.
- push copies a spec folder's decision-bearing files (spec.md, proposal.md,
  plan.md, design.md, research.md) to the wiki folder specs/NAME/. NAME is the
  folder's name, without the date an OpenSpec archive adds (2026-11-26-).
  Tasks, contracts, data models and the rest are build-time only.
  --prune also removes the folder's other pages (asks unless --yes).
- pull copies the spec pages of ticket REF (#123, group/app#123, an issue URL,
  or ENG-123) into FOLDER. The wiki folder is the one named for that ticket
  (123-add-login, app-123-add-login, eng-123-add-login). Existing files are
  kept unless --yes.
- pull-doc and push-docs move the project docs. A file whose first "# " heading
  is "Product Map" is the page Product-Map.md at the wiki's root, which the
  wiki shows as "Product Map".
- A write is one commit, pushed at once. A push that loses a race with another
  writer is retried once on top of the new wiki.
- CODEKIT_WIKI_TOKEN, when set (CI), authenticates over HTTPS. It's passed to
  git through the environment, never written to disk or printed. Otherwise
  git's own credentials are used. git never prompts.

Standard library only, so it runs with any Python 3.10+.
"""

import argparse
import base64
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

DOC_ORDER = (
    "spec.md",
    "proposal.md",
    "plan.md",
    "design.md",
    "research.md",
)
SPECS = "specs"
ARCHIVE_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}-")
HEADING = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
SCP_LIKE = re.compile(r"^(?:[^@/]+@)?(?P<host>[^:/]+):(?P<path>[^/].*)$")
URL_FORM = re.compile(
    r"^(?P<scheme>[a-z][a-z0-9+.-]*)://(?:(?P<userinfo>[^@/]*)@)?"
    r"(?P<host>[^/:]+)(?::(?P<port>\d+))?/(?P<path>.+)$",
    re.IGNORECASE,
)
ISSUE_URL = re.compile(r"^https?://[^/]+/(?P<path>.+?)/-/(?:issues|work_items)/(?P<n>\d+)")
ISSUE_REF = re.compile(r"^(?P<path>[\w.\-/]+)?#(?P<n>\d+)$")
CREDENTIALS = re.compile(r"(?<=://)[^/@\s]+@")
# The wiki clone is codekit's own scratch repo: the user's commit signing and
# hooks don't apply to it, and a signing prompt would hang with no terminal.
SCRATCH = ("-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null")


def redact(text: str) -> str:
    """Text with any user:password@ taken out of the URLs in it."""
    return CREDENTIALS.sub("", text)


class WikiError(SystemExit):
    """Stop with a message for the user (exit status 1). Credentials never show."""

    def __init__(self, message: str) -> None:
        super().__init__(redact(message))


def git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    token = os.environ.get("CODEKIT_WIKI_TOKEN", "").strip()
    if token:
        basic = base64.b64encode(f"oauth2:{token}".encode()).decode()
        env |= {
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "http.extraHeader",
            "GIT_CONFIG_VALUE_0": f"Authorization: Basic {basic}",
        }
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, env=env
    )
    if check and result.returncode != 0:
        last = (result.stderr.strip().splitlines() or ["(no output)"])[-1]
        raise WikiError(f"git {args[0]} failed: {last}")
    return result


def out(cwd: Path, *args: str) -> str:
    return git(cwd, *args, check=False).stdout.strip()


def project_root() -> Path:
    top = out(Path.cwd(), "rev-parse", "--show-toplevel")
    if not top:
        raise WikiError("Not in a git repo: run this from the project root.")
    return Path(top)


class Remote:
    """The code's origin remote, and the wiki repo and pages next to it."""

    def __init__(self, url: str) -> None:
        self.url = url.strip().rstrip("/")
        match = URL_FORM.match(self.url)
        scp = None if match or "://" in self.url else SCP_LIKE.match(self.url)
        if match:
            self.scheme = match["scheme"].lower()
            self.host = match["host"]
            self.port = match["port"]
            self.userinfo = match["userinfo"]
            path = match["path"]
        elif scp:
            self.scheme, self.host, self.port, self.userinfo = "ssh", scp["host"], None, None
            path = scp["path"]
        else:  # a local path, as in tests
            self.scheme, self.host, self.port, self.userinfo = "file", "", None, None
            path = self.url
        self.path = path[:-4] if path.endswith(".git") else path

    @property
    def wiki_url(self) -> str:
        """The wiki's git URL. With a token, HTTPS without any stored credentials."""
        token = os.environ.get("CODEKIT_WIKI_TOKEN", "").strip()
        base = self.url[:-4] if self.url.endswith(".git") else self.url
        if token and self.scheme != "file":
            scheme = self.scheme if self.scheme in ("http", "https") else "https"
            port = f":{self.port}" if self.port and scheme == self.scheme else ""
            return f"{scheme}://{self.host}{port}/{self.path}.wiki.git"
        return f"{base}.wiki.git"

    def page_url(self, page: str) -> str:
        """Where a page shows in the browser (GitLab's layout)."""
        if self.scheme == "file":
            return f"{self.wiki_url}:{page}"
        scheme = self.scheme if self.scheme in ("http", "https") else "https"
        port = f":{self.port}" if self.port and scheme == self.scheme else ""
        slug = page[:-3] if page.endswith(".md") else page
        return f"{scheme}://{self.host}{port}/{self.path}/-/wikis/{slug}"


def origin(root: Path) -> Remote:
    url = out(root, "remote", "get-url", "origin")
    if not url:
        raise WikiError("No origin remote: the wiki is found from it.")
    return Remote(url)


def default_branch(cwd: Path, wiki_url: str) -> tuple[str, bool]:
    """The wiki's branch, and whether the wiki has any pages yet."""
    result = git(cwd, "ls-remote", "--symref", wiki_url, "HEAD", check=False)
    if result.returncode != 0:
        last = (result.stderr.strip().splitlines() or ["(no output)"])[-1]
        raise WikiError(
            f"Can't reach the wiki at {wiki_url}: {last}\n"
            "Check that the project's wiki is turned on (Settings > General > "
            "Visibility, project features, permissions) and that you can push "
            "to the code. If the wiki has never had a page, create its first one "
            "in GitLab (Plan > Wiki > Create your first page) and run this again."
        )
    match = re.search(r"^ref: refs/heads/(\S+)\s+HEAD", result.stdout, re.MULTILINE)
    if match:
        return match.group(1), True
    heads = out(cwd, "ls-remote", "--heads", wiki_url).splitlines()
    names = [line.split("refs/heads/", 1)[-1] for line in heads if "refs/heads/" in line]
    for name in ("main", "master", *names):
        if name in names:
            return name, True
    return "main", False


def refresh(wiki: Path, branch: str) -> None:
    """Bring a reused clone to the wiki's current state, whatever a past run left."""
    git(wiki, "rebase", "--abort", check=False)
    git(wiki, "fetch", "--quiet", "origin", branch)
    git(wiki, "checkout", "--quiet", "--force", "-B", branch, "FETCH_HEAD")
    git(wiki, "reset", "--quiet", "--hard", "FETCH_HEAD")
    git(wiki, "clean", "-fdxq")


def checkout(root: Path, remote: Remote) -> tuple[Path, str]:
    """A clean, current clone of this project's wiki in the temp folder, and its branch.

    A clone is reused only when it's of this same wiki and the wiki has pages.
    Anything else (another project with the same folder name, an empty wiki,
    a clone a failed run left broken) starts from a fresh clone.
    """
    wiki = Path(os.environ.get("TMPDIR") or "/tmp") / "codekit" / root.name / "wiki"
    branch, has_pages = default_branch(root, remote.wiki_url)
    same_wiki = (wiki / ".git").is_dir() and out(wiki, "remote", "get-url", "origin") == remote.wiki_url
    if same_wiki and has_pages:
        try:
            refresh(wiki, branch)
            return wiki, branch
        except WikiError:
            pass
    shutil.rmtree(wiki, ignore_errors=True)
    wiki.parent.mkdir(parents=True, exist_ok=True)
    git(wiki.parent, "clone", "--quiet", remote.wiki_url, wiki.name)
    if has_pages:
        git(wiki, "checkout", "--quiet", "-B", branch, f"origin/{branch}")
    else:
        git(wiki, "symbolic-ref", "HEAD", f"refs/heads/{branch}")
    return wiki, branch


def publish(wiki: Path, branch: str, message: str) -> None:
    """Commit everything in the clone and push it, retrying once on top of a newer wiki."""
    git(wiki, "add", "-A")
    if not out(wiki, "status", "--porcelain"):
        return
    options = list(SCRATCH)
    if not out(wiki, "config", "user.email"):
        options += ["-c", "user.name=codekit", "-c", "user.email=codekit@localhost"]
    git(wiki, *options, "commit", "--quiet", "-m", message)
    if git(wiki, "push", "--quiet", "origin", f"HEAD:{branch}", check=False).returncode == 0:
        return
    rebased = git(wiki, *options, "pull", "--quiet", "--rebase", "origin", branch, check=False)
    if rebased.returncode != 0:
        git(wiki, "rebase", "--abort", check=False)
        raise WikiError(
            "Someone changed the same wiki pages while this ran, so nothing was "
            "written. Run it again: it starts from the wiki as it is now."
        )
    git(wiki, "push", "--quiet", "origin", f"HEAD:{branch}")


def page_file(title: str) -> str:
    """GitLab stores a page titled "Product Map" as Product-Map.md."""
    return title.strip().replace(" ", "-") + ".md"


def title_of(path: Path, content: str) -> str:
    match = HEADING.search(content)
    return match.group(1) if match else path.stem


def spec_name(folder: Path) -> str:
    return ARCHIVE_DATE.sub("", folder.name)


def ticket_prefix(ref: str, project_path: str) -> str:
    """The folder-name prefix sdd-plan gives a ticket: 123, app-123, or eng-123."""
    ref = ref.strip()
    match = ISSUE_URL.match(ref) or ISSUE_REF.match(ref)
    if not match:
        return ref.lower()
    path = (match["path"] or "").strip("/")
    if not path or path == project_path:
        return match["n"]
    return f"{path.rsplit('/', 1)[-1].lower()}-{match['n']}"


def plan(sources: list[str], targets: list[Path]) -> list[str]:
    """create, update, or unchanged for each source against its page in the clone."""
    kinds = []
    for content, target in zip(sources, targets):
        if not target.exists():
            kinds.append("create")
        elif target.read_text(encoding="utf-8") == content:
            kinds.append("unchanged")
        else:
            kinds.append("update")
    return kinds


def display(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root))
    except ValueError:
        return str(path)


def confirm(question: str) -> bool:
    try:
        answer = input(f"{question} [y/N] ")
    except EOFError:
        answer = ""
    return answer.strip().lower() in ("y", "yes")


def cmd_check(root: Path, remote: Remote) -> int:
    _, has_pages = default_branch(root, remote.wiki_url)
    state = "ok" if has_pages else "ok (no pages yet)"
    print(f"wiki {state}: {remote.page_url('home')}")
    return 0


def cmd_push(root: Path, remote: Remote, args: argparse.Namespace) -> int:
    folder = args.folder.resolve()
    if not folder.is_dir():
        raise WikiError(f"No spec folder at {display(folder, root)}.")
    names = [n for n in DOC_ORDER if (folder / n).is_file()]
    if not names:
        print(f"No spec files in {display(folder, root)}; nothing to sync.")
        return 1
    sources = [(folder / n).read_text(encoding="utf-8") for n in names]
    name = args.name or spec_name(folder)
    wiki, branch = checkout(root, remote)
    target_dir = wiki / SPECS / name
    targets = [target_dir / n for n in names]
    kinds = plan(sources, targets)
    deletes = []
    if args.prune and target_dir.is_dir():
        deletes = [p for p in sorted(target_dir.iterdir()) if p.is_file() and p.name not in names]
    print(f"{remote.page_url(f'{SPECS}/{name}')}  <- {display(folder, root)}")
    for kind, target in zip(kinds, targets):
        print(f"  {kind:<9} {target.name}")
    for path in deletes:
        print(f"  {'delete':<9} {path.name}")
    if args.dry_run:
        print("Dry run: nothing written.")
        return 0
    if deletes and not args.yes and not confirm(f"Delete {len(deletes)} page(s) from the wiki?"):
        print("Stopped: nothing written.")
        return 1
    target_dir.mkdir(parents=True, exist_ok=True)
    for content, target in zip(sources, targets):
        target.write_text(content, encoding="utf-8")
    for path in deletes:
        path.unlink()
    changed = sum(kind != "unchanged" for kind in kinds) + len(deletes)
    if changed:
        publish(wiki, branch, f"codekit: {SPECS}/{name}")
    print(f"Done: {changed} change(s).")
    return 0


def cmd_pull(root: Path, remote: Remote, args: argparse.Namespace) -> int:
    wiki, _ = checkout(root, remote)
    prefix = ticket_prefix(args.issue, remote.path)
    specs = wiki / SPECS
    folders = sorted(specs.iterdir()) if specs.is_dir() else []
    matches = [
        d for d in folders
        if d.is_dir() and (d.name == prefix or d.name.startswith(f"{prefix}-"))
    ]
    folder = args.folder.resolve()
    if not matches:
        print(f"{args.issue}  -> {display(folder, root)}")
        print("  none      (the wiki has no spec pages for this ticket)")
        return 0
    if len(matches) > 1:
        def last_change(d: Path) -> int:
            stamp = out(wiki, "log", "-1", "--format=%ct", "--", str(d.relative_to(wiki)))
            return int(stamp or 0)

        matches.sort(key=last_change, reverse=True)
        others = ", ".join(d.name for d in matches[1:])
        print(f"several wiki folders for {args.issue}; using the newest, {matches[0].name} (also {others})")
    source = matches[0]
    folder.mkdir(parents=True, exist_ok=True)
    print(f"{remote.page_url(f'{SPECS}/{source.name}')}  -> {display(folder, root)}")
    for name in DOC_ORDER:
        page = source / name
        if not page.is_file():
            continue
        target = folder / name
        if target.exists() and not args.yes:
            print(f"  kept      {name} (exists locally)")
            continue
        shutil.copyfile(page, target)
        print(f"  pulled    {name}")
    return 0


def cmd_pull_doc(root: Path, remote: Remote, args: argparse.Namespace) -> int:
    wiki, _ = checkout(root, remote)
    page = wiki / page_file(args.title)
    if not page.is_file():
        print(f"missing  {args.title} (not in the wiki)")
        return 0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(page, args.out)
    print(f"pulled   {args.title} -> {args.out}")
    return 0


def cmd_push_docs(root: Path, remote: Remote, args: argparse.Namespace) -> int:
    missing = [str(p) for p in args.files if not p.is_file()]
    if not args.files or missing:
        raise WikiError(f"push-docs needs existing files; missing: {', '.join(missing) or 'none given'}")
    wiki, branch = checkout(root, remote)
    sources = [p.read_text(encoding="utf-8") for p in args.files]
    titles = [title_of(p, c) for p, c in zip(args.files, sources)]
    targets = [wiki / page_file(t) for t in titles]
    kinds = plan(sources, targets)
    print(remote.page_url("home"))
    for kind, title, target in zip(kinds, titles, targets):
        print(f"  {kind:<9} {title}  {remote.page_url(target.name)}")
    if args.dry_run:
        print("Dry run: nothing written.")
        return 0
    for content, target in zip(sources, targets):
        target.write_text(content, encoding="utf-8")
    changed = sum(kind != "unchanged" for kind in kinds)
    if changed:
        publish(wiki, branch, "codekit: project docs")
    print(f"Done: {changed} change(s).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    push = sub.add_parser("push")
    push.add_argument("folder", type=Path)
    push.add_argument("--name")
    push.add_argument("--prune", action="store_true")
    push.add_argument("--yes", action="store_true")
    push.add_argument("--dry-run", action="store_true")
    pull = sub.add_parser("pull")
    pull.add_argument("folder", type=Path)
    pull.add_argument("--issue", required=True)
    pull.add_argument("--yes", action="store_true")
    pull_doc = sub.add_parser("pull-doc")
    pull_doc.add_argument("--title", required=True)
    pull_doc.add_argument("--out", type=Path, required=True)
    push_docs = sub.add_parser("push-docs")
    push_docs.add_argument("files", nargs="+", type=Path)
    push_docs.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    root = project_root()
    remote = origin(root)
    commands = {
        "check": lambda: cmd_check(root, remote),
        "push": lambda: cmd_push(root, remote, args),
        "pull": lambda: cmd_pull(root, remote, args),
        "pull-doc": lambda: cmd_pull_doc(root, remote, args),
        "push-docs": lambda: cmd_push_docs(root, remote, args),
    }
    return commands[args.command]()


if __name__ == "__main__":
    sys.exit(main())
