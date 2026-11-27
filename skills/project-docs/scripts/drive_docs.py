#!/usr/bin/env python3
"""
Copy the project docs into a Google Drive folder as Google Docs, for people
who can't open the tracker or the repo. Drive is a one-way copy: nothing
reads it back.

    python3 drive_docs.py push FILE [FILE ...] [--folder ID]

- Each FILE becomes the Google Doc in the folder named by the file's first
  "# " heading (else the file name). It's created if the folder has none,
  otherwise replaced whole, so its link never changes. A missing FILE is
  skipped.
- The folder is --folder, else `git config codekit.drive`, else that key in
  the committed .config/.gitconfig. A folder link works as well as its ID.
  With no folder, it says so and exits 0, so a CI job can always run it.
- It logs in with an OAuth refresh token from the environment:
  CODEKIT_DRIVE_CLIENT_ID, CODEKIT_DRIVE_CLIENT_SECRET, and
  CODEKIT_DRIVE_REFRESH_TOKEN. The token's Google account needs Editor on the
  folder. No credential is ever printed.

Standard library only, so it runs with any Python 3.10+.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path
from urllib import error, parse, request

TOKEN_URL = "https://oauth2.googleapis.com/token"
FILES = "https://www.googleapis.com/drive/v3/files"
UPLOAD = "https://www.googleapis.com/upload/drive/v3/files"
DOC = "application/vnd.google-apps.document"
FOLDER = "application/vnd.google-apps.folder"
CREDENTIALS = (
    "CODEKIT_DRIVE_CLIENT_ID",
    "CODEKIT_DRIVE_CLIENT_SECRET",
    "CODEKIT_DRIVE_REFRESH_TOKEN",
)
HEADING = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
FOLDER_LINK = re.compile(r"(?:/folders/|[?&]id=)([\w-]+)")
FOLDER_ID = re.compile(r"[\w-]+")
NOTE = "> A copy made by codekit. Edits made here are overwritten on the next update."
SETUP = "See codekit's docs/SETUP.md, Google Drive copy."


class DriveError(SystemExit):
    """Stop with a message for the user (exit status 1)."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Drive: {message}")


class GoogleError(Exception):
    def __init__(self, code: int, reason: str) -> None:
        super().__init__(f"Google returned {code}: {reason}")
        self.code = code
        self.reason = reason


def git(*args: str) -> str:
    try:
        result = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def folder_setting() -> str:
    """codekit.drive from git config, else from the committed .config/.gitconfig.

    The committed file covers CI and fresh clones, where the include isn't wired.
    """
    root = git("rev-parse", "--show-toplevel") or "."
    return git("config", "codekit.drive") or git(
        "config", "--file", f"{root}/.config/.gitconfig", "codekit.drive"
    )


def folder_id(value: str) -> str:
    match = FOLDER_LINK.search(value)
    if match:
        return match.group(1)
    if FOLDER_ID.fullmatch(value):
        return value
    raise DriveError(f"{value!r} isn't a Drive folder link or ID.")


def title_of(path: Path, content: str) -> str:
    match = HEADING.search(content)
    return match.group(1) if match else path.stem


def with_note(content: str) -> str:
    """The doc with NOTE under its title, so readers know where edits go."""
    match = HEADING.search(content)
    if not match:
        return f"{NOTE}\n\n{content}"
    end = match.end(1)
    return f"{content[:end]}\n\n{NOTE}{content[end:]}"


def reason_of(exc: error.HTTPError) -> str:
    text = exc.read().decode("utf-8", errors="replace")
    try:
        data = json.loads(text)
    except ValueError:
        return text.strip()[:300]
    err = data.get("error")
    if isinstance(err, dict):
        return str(err.get("message") or err)
    return " ".join(str(part) for part in (err, data.get("error_description")) if part)


def call(
    method: str,
    url: str,
    token: str = "",
    body: bytes | None = None,
    content_type: str = "",
) -> dict:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if content_type:
        headers["Content-Type"] = content_type
    req = request.Request(url, data=body, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8") or "{}")
    except error.HTTPError as exc:
        raise GoogleError(exc.code, reason_of(exc)) from None
    except (error.URLError, TimeoutError) as exc:
        raise DriveError(f"can't reach Google: {getattr(exc, 'reason', exc)}") from None


def access_token() -> str:
    values = {name: os.environ.get(name, "").strip() for name in CREDENTIALS}
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise DriveError(f"codekit.drive is set, but these aren't: {', '.join(missing)}. {SETUP}")
    body = parse.urlencode(
        {
            "client_id": values["CODEKIT_DRIVE_CLIENT_ID"],
            "client_secret": values["CODEKIT_DRIVE_CLIENT_SECRET"],
            "refresh_token": values["CODEKIT_DRIVE_REFRESH_TOKEN"],
            "grant_type": "refresh_token",
        }
    ).encode("utf-8")
    try:
        data = call("POST", TOKEN_URL, body=body, content_type="application/x-www-form-urlencoded")
    except GoogleError as exc:
        hint = ""
        if "invalid_grant" in exc.reason:
            hint = (
                " The refresh token was revoked, or it expired because the OAuth"
                " client is still in Testing. Publish it, then create a new token."
            )
        elif "invalid_client" in exc.reason:
            hint = " Check CODEKIT_DRIVE_CLIENT_ID and CODEKIT_DRIVE_CLIENT_SECRET."
        raise DriveError(f"Google refused the login ({exc.reason}).{hint} {SETUP}") from None
    return data["access_token"]


def check_folder(token: str, folder: str) -> str:
    params = parse.urlencode(
        {"fields": "name,mimeType,capabilities(canAddChildren)", "supportsAllDrives": "true"}
    )
    try:
        meta = call("GET", f"{FILES}/{folder}?{params}", token)
    except GoogleError as exc:
        if exc.code == 404:
            raise DriveError(
                f"can't see folder {folder}. Check codekit.drive, and that the folder"
                " is shared with the token's Google account as Editor."
            ) from None
        raise
    name = meta.get("name", folder)
    if meta.get("mimeType") != FOLDER:
        raise DriveError(f"{name} ({folder}) isn't a folder.")
    if not meta.get("capabilities", {}).get("canAddChildren"):
        raise DriveError(f"the token's Google account can't add files to {name}. Share it as Editor.")
    return name


def find_docs(token: str, folder: str, title: str) -> list[dict]:
    """The folder's Google Docs with this title, newest first."""
    name = title.replace("\\", "\\\\").replace("'", "\\'")
    query = f"name = '{name}' and '{folder}' in parents and mimeType = '{DOC}' and trashed = false"
    params = parse.urlencode(
        {
            "q": query,
            "fields": "files(id,webViewLink)",
            "orderBy": "modifiedTime desc",
            "supportsAllDrives": "true",
            "includeItemsFromAllDrives": "true",
        }
    )
    return call("GET", f"{FILES}?{params}", token).get("files", [])


def create(token: str, folder: str, title: str, content: str) -> dict:
    """A new Google Doc converted from the markdown."""
    boundary = uuid.uuid4().hex
    meta = json.dumps({"name": title, "mimeType": DOC, "parents": [folder]})
    body = (
        f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{meta}\r\n"
        f"--{boundary}\r\nContent-Type: text/markdown; charset=UTF-8\r\n\r\n{content}\r\n"
        f"--{boundary}--\r\n"
    ).encode("utf-8")
    params = parse.urlencode(
        {"uploadType": "multipart", "supportsAllDrives": "true", "fields": "id,webViewLink"}
    )
    return call("POST", f"{UPLOAD}?{params}", token, body, f"multipart/related; boundary={boundary}")


def replace(token: str, file_id: str, content: str) -> dict:
    """The Google Doc's whole content replaced by the markdown. Its ID and link stay."""
    params = parse.urlencode(
        {"uploadType": "media", "supportsAllDrives": "true", "fields": "id,webViewLink"}
    )
    return call(
        "PATCH",
        f"{UPLOAD}/{file_id}?{params}",
        token,
        content.encode("utf-8"),
        "text/markdown; charset=UTF-8",
    )


def push(files: list[Path], folder_value: str | None) -> int:
    value = folder_value or folder_setting()
    if not value:
        print("Drive: codekit.drive isn't set, so there's nothing to copy.")
        return 0
    folder = folder_id(value)
    present = [path for path in files if path.is_file()]
    if not present:
        raise DriveError(f"none of these files exist: {', '.join(map(str, files))}")
    token = access_token()
    name = check_folder(token, folder)
    print(f"Drive folder {name}: https://drive.google.com/drive/folders/{folder}")
    for path in files:
        if path not in present:
            print(f"  skipped  {path} (no such file)")
            continue
        content = path.read_text(encoding="utf-8")
        title = title_of(path, content)
        found = find_docs(token, folder, title)
        if found:
            doc, kind = replace(token, found[0]["id"], with_note(content)), "updated"
        else:
            doc, kind = create(token, folder, title, with_note(content)), "created"
        print(f"  {kind:<8} {title}  {doc.get('webViewLink', '')}")
        if len(found) > 1:
            print(
                f"  The folder has {len(found)} docs named {title!r}."
                " The newest was updated; delete the others."
            )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("command", choices=("push",))
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--folder", help="the folder's ID or link (default: codekit.drive)")
    args = parser.parse_args(argv)
    try:
        return push(args.files, args.folder)
    except GoogleError as exc:
        raise DriveError(str(exc)) from None


if __name__ == "__main__":
    sys.exit(main())
