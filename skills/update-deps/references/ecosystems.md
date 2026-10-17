# Per-ecosystem commands

Read the section for each ecosystem you detected. Each section covers: how to detect it, how to list outdated packages, how to bump a package so the manifest constraint moves (not just the lockfile), how to install, and ecosystem-specific traps.

## Transitive refresh (run after the named upgrades, every ecosystem)

Named upgrades hold every other locked version in place. These commands move everything the manifests already allow, without crossing any declared range:

| Ecosystem | Command |
|---|---|
| uv | `uv lock --upgrade` then `uv sync --all-packages --all-groups` |
| poetry | `poetry update` |
| pip / pip-tools | `pip-compile --upgrade` (only if `requirements.in` exists; plain pins do not move) |
| bun | `bun update` (no `--latest`) |
| npm | `npm update` |
| pnpm | `pnpm update` (`-r` for workspaces) |
| yarn | `yarn upgrade` (classic) / `yarn up -R '*'` (berry) |
| cargo | `cargo update` |
| go | `go get -u ./... && go mod tidy` |

Contents:
- [Transitive refresh](#transitive-refresh-run-after-the-named-upgrades-every-ecosystem)
- [Python: uv](#python-uv)
- [Python: poetry](#python-poetry)
- [Python: pip / requirements.txt](#python-pip--requirementstxt)
- [JavaScript: bun](#javascript-bun)
- [JavaScript: npm](#javascript-npm)
- [JavaScript: pnpm](#javascript-pnpm)
- [JavaScript: yarn](#javascript-yarn)
- [Rust: cargo](#rust-cargo)
- [Go: modules](#go-modules)
- [Finding release notes](#finding-release-notes)

---

## Python: uv

**Detect:** `uv.lock` next to a `pyproject.toml`. A `[tool.uv.workspace]` table with `members` means a workspace: one lockfile at the root, several `pyproject.toml` files below it.

**List outdated (direct deps only, all workspace members at once):**
```bash
uv tree --outdated --depth 1
```
Lines look like `├── fastapi[standard] v0.139.0 (latest: v0.141.1)`. Lines without `(latest: ...)` are current. Dependency groups show as `(group: dev)`.

**Bump one package so the constraint in pyproject.toml moves:**
```bash
# root project
uv add "fastapi>=0.141.1" --upgrade-package fastapi
# a workspace member (run from the root, or cd into the member dir)
uv add --package service "fastapi>=0.141.1" --upgrade-package fastapi
# a dependency group (e.g. dev)
uv add --group dev "ruff>=0.16.8" --upgrade-package ruff
# an optional extra
uv add --optional docs "mkdocs>=2" --upgrade-package mkdocs
```
Keep the extras the project already declares: if the manifest has `fastapi[standard]`, bump with `"fastapi[standard]>=0.141.1"` or the extras get dropped.

Keep the constraint style the project uses. Most uv projects use `>=`; if the project uses `~=` or `==` pins, match that.

**Lockfile-only upgrade (within existing constraints; useful for transitive deps):**
```bash
uv lock --upgrade-package <name>
uv lock --upgrade            # everything, within constraints
```
This alone is not enough for a "bump to latest" request when the manifest has an upper bound.

**Install and verify:**
```bash
uv sync --all-packages --all-groups     # workspace
uv sync --all-groups                    # single project
```

**Traps:**
- Same package in several members must move together; edit each member's constraint, then one `uv lock`.
- `requires-python` in the manifest is a hard floor. A package that now needs 3.13 will not resolve on a 3.12 project; that is a card, not a safe update.
- Projects that ship a `requirements.txt` for a platform (App Engine, Cloud Functions) usually regenerate it with `uv export`; look for a Makefile target and run it after the install.

---

## Python: poetry

**Detect:** `poetry.lock`, `[tool.poetry]` in `pyproject.toml`.

**List outdated:**
```bash
poetry show --outdated --top-level
```

**Bump so the constraint moves:**
```bash
poetry add "fastapi@latest"
poetry add --group dev "ruff@latest"
```
Poetry writes a caret constraint (`^0.141.1`) by default. If the project uses a different style, edit `pyproject.toml` directly and run `poetry lock` then `poetry install`.

**Install:** `poetry install --with dev` (or `--all-groups` on Poetry 2.x).

---

## Python: pip / requirements.txt

**Detect:** `requirements*.txt` with no `uv.lock` or `poetry.lock`. Possibly `requirements.in` with pip-tools.

**List outdated:**
```bash
pip list --outdated --format=columns
```
Run inside the project's virtualenv. If there is none, create one and `pip install -r requirements.txt` first so the listing reflects the project, not the machine.

**Bump:** edit the file in place. Pins stay pins (`==`), ranges stay ranges. If `requirements.in` exists, edit that and run `pip-compile`.

**Install:** `pip install -r requirements.txt` (and `-r requirements-dev.txt` if present).

---

## JavaScript: bun

**Detect:** `bun.lock` or `bun.lockb` next to `package.json`.

**List outdated (all workspaces):**
```bash
bun outdated
```
Columns: Current, Update (latest within the declared range), Latest. A Latest that differs from Update is a range-crossing bump.

**Bump so package.json moves:**
```bash
bun update --latest                 # everything, rewrites package.json ranges to the new versions
bun update --latest react react-dom # named packages only
bun update --latest --dry-run       # preview
```
`bun update` **without** `--latest` stays inside the declared semver ranges and will not perform a major bump. Do not use it for the safe batch either if any range is already at its ceiling; prefer `--latest` with an explicit list of the safe packages.

To pin to a specific version rather than latest: `bun update zod@3.25.0`.

Bun rewrites ranges in the same style the project had (`^` stays `^`, `~` stays `~`). Tilde ranges are usually a deliberate hold; flag them.

**Install:** `bun install`.

**Traps:**
- Peer dependency errors at install usually mean a plugin has not caught up to its host's new major. Bump host and plugins together or hold them together.
- `engines.node` in package.json is the runtime floor.

---

## JavaScript: npm

**Detect:** `package-lock.json`.

**List outdated:**
```bash
npm outdated
```
Columns: Current, Wanted (within range), Latest.

**Bump so package.json moves:** npm's own `npm update` does not rewrite package.json for major bumps. Use npm-check-updates:
```bash
npx npm-check-updates            # preview everything
npx npm-check-updates --target minor   # safe batch: minor and patch only
npx npm-check-updates -u <pkg> <pkg>   # write chosen packages to package.json
npm install
```
Or edit `package.json` by hand and `npm install`.

**Workspaces:** `npm outdated --workspaces` and `npx npm-check-updates --workspaces`.

---

## JavaScript: pnpm

**Detect:** `pnpm-lock.yaml`.

**List outdated:** `pnpm outdated` (add `-r` for all workspace packages).

**Bump so package.json moves:**
```bash
pnpm update --latest                    # everything
pnpm update --latest <pkg> <pkg>        # named
pnpm update --latest -r                 # all workspace packages
pnpm update -i --latest                 # interactive picker
```
Without `--latest`, pnpm stays inside declared ranges, same as bun.

**Install:** `pnpm install`.

---

## JavaScript: yarn

**Detect:** `yarn.lock`. Check the version: `yarn --version`. Berry (2+) and classic (1.x) differ.

**Classic (1.x):**
```bash
yarn outdated
yarn upgrade --latest <pkg>      # rewrites package.json
yarn upgrade-interactive --latest
```

**Berry (2+):**
```bash
yarn upgrade-interactive         # needs the interactive-tools plugin on v2/v3; built in on v4
yarn up <pkg>                    # bumps to latest, rewrites package.json
yarn up '<pkg>@^X.Y.Z'           # to a specific range
```

---

## Rust: cargo

**Detect:** `Cargo.toml` and `Cargo.lock`.

**List outdated:** requires `cargo-outdated` or `cargo-edit`:
```bash
cargo outdated --root-deps-only       # cargo install cargo-outdated
cargo upgrade --dry-run               # cargo install cargo-edit
```
If neither is installed, ask before installing a global tool, or read the Cargo.toml and check crates.io per crate.

**Bump so Cargo.toml moves:**
```bash
cargo upgrade                         # everything, within compatible ranges
cargo upgrade --incompatible          # include major bumps
cargo upgrade -p <crate>
```
`cargo update` alone only moves `Cargo.lock` within declared ranges.

**Verify:** `cargo build && cargo test && cargo clippy` (if clippy is used).

**Traps:** `rust-version` in Cargo.toml is the toolchain floor (MSRV); crates often raise theirs in minor releases.

---

## Go: modules

**Detect:** `go.mod`.

**List outdated (direct deps):**
```bash
go list -m -u -f '{{if and (not .Indirect) .Update}}{{.Path}} {{.Version}} -> {{.Update.Version}}{{end}}' all
```

**Bump:**
```bash
go get <module>@latest        # one module, rewrites go.mod
go get -u ./...               # all direct and indirect, minor and patch only
go mod tidy
```
A Go major bump is a new import path (`/v2`, `/v3`), so it is always a code change. `go get -u` never crosses majors. Treat every major as a card and expect to rewrite imports; `gofmt -r` or a sed over the import path handles the mechanical part.

**Verify:** `go build ./... && go vet ./... && go test ./...`.

---

## Finding release notes

In order of preference:

1. **Context7 MCP** if available: `resolve-library-id` with the package name, then `query-docs` with "breaking changes in vX" or "migrating from vX to vY". Fast and already summarized.
2. **GitHub releases page**: `https://github.com/<org>/<repo>/releases`. The repo URL is in the package metadata (`uv pip show <pkg>`, `npm view <pkg> repository.url`, `cargo info <crate>`, `pkg.go.dev/<module>`).
3. **CHANGELOG.md** in the repo root, or a `docs/migration` page. Django, ESLint, Pydantic, React Router, and most large projects maintain a dedicated migration guide for each major; search for "<package> vX migration guide".
4. **Registry page** as a last resort: pypi.org, npmjs.com, crates.io.

Read only the span between the project's current version and the latest. A v3 to v5 jump means reading the v4 notes too.
