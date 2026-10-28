.DEFAULT_GOAL := help

# ── Help ──────────────────────────────────────────────────────────────────────

.PHONY: help
help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*##"}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' \
		| sort

# ── Setup ─────────────────────────────────────────────────────────────────────

.PHONY: setup
setup: hooks antigravity claude ## First-time dev setup: install hooks, Antigravity plugin, Claude plugin

.PHONY: hooks
hooks: ## Install pre-commit hooks and the commit template
	@command -v uv >/dev/null 2>&1 \
		&& uv tool install pre-commit --quiet \
		|| pip install --quiet pre-commit
	pre-commit install --config .config/.pre-commit-config.yaml
	@git config --local commit.template .config/.commit-message-template
	@echo "✓ pre-commit hooks installed"

# ── Antigravity ───────────────────────────────────────────────────────────────
# Two products, same plugin contents, different install surface:
#   IDE (v2.x)      — folder placement, no command. Symlink for live reload.
#   CLI (agy, v1.x) — `agy plugin install`, own dir under ~/.gemini/antigravity-cli/

ANTIGRAVITY_PLUGINS ?= $(HOME)/.gemini/config/plugins

.PHONY: antigravity
antigravity: antigravity-ide antigravity-cli ## Install for Antigravity IDE + CLI (whichever are present)

.PHONY: antigravity-ide
antigravity-ide: ## Symlink into the Antigravity IDE global plugin dir (live reloads on changes)
	@mkdir -p $(ANTIGRAVITY_PLUGINS)
	@ln -sfn $(PWD) $(ANTIGRAVITY_PLUGINS)/codekit
	@echo "✓ Antigravity IDE plugin linked: $(ANTIGRAVITY_PLUGINS)/codekit -> $(PWD)"
	@echo "  Restart the IDE, then run /sdd-plan to confirm skills load."

.PHONY: antigravity-cli
antigravity-cli: ## Install into Antigravity CLI via `agy plugin install`
	@command -v agy >/dev/null 2>&1 \
		&& { agy plugin install $(PWD) && echo "✓ Antigravity CLI plugin installed (agy plugin list to verify)"; } \
		|| echo "⊘ agy not found — skipping CLI install (https://antigravity.google/cli/install.sh)"

.PHONY: antigravity-workspace
antigravity-workspace: ## Symlink into a workspace's .agents/plugins/ (set DIR=/path/to/workspace)
	@test -n "$(DIR)" || { echo "Usage: make antigravity-workspace DIR=/path/to/workspace"; exit 1; }
	@mkdir -p $(DIR)/.agents/plugins
	@ln -sfn $(PWD) $(DIR)/.agents/plugins/codekit
	@echo "✓ Antigravity plugin linked: $(DIR)/.agents/plugins/codekit -> $(PWD)"

.PHONY: un-antigravity
un-antigravity: ## Remove the Antigravity IDE symlink and uninstall from the CLI
	@rm -f $(ANTIGRAVITY_PLUGINS)/codekit
	@echo "✓ Antigravity IDE plugin unlinked"
	@command -v agy >/dev/null 2>&1 \
		&& { agy plugin uninstall codekit && echo "✓ Antigravity CLI plugin uninstalled"; } \
		|| echo "⊘ agy not found — nothing to uninstall"

# ── Claude ────────────────────────────────────────────────────────────────────

.PHONY: claude
claude: ## Install this repo as a Claude plugin (local scope, this machine only)
	claude plugin marketplace add $(PWD)
	claude plugin install codekit@codekit-marketplace
	@echo "✓ Claude plugin installed — run /mcp and authenticate 'linear'"

.PHONY: un-claude
un-claude: ## Uninstall the local Claude plugin
	claude plugin uninstall codekit --scope local
	@echo "✓ Claude plugin uninstalled"

# ── SDD frameworks (optional, per consumer project) ──────────────────────────

.PHONY: speckit
speckit: ## Install the SpecKit CLI (specify)
	uv tool install specify-cli --from git+https://github.com/github/spec-kit.git

.PHONY: openspec
openspec: ## Install the OpenSpec CLI
	npm install -g @fission-ai/openspec@latest

# ── Validation ────────────────────────────────────────────────────────────────

.PHONY: check
check: ## Run pre-commit checks on all files
	pre-commit run --all-files --config .config/.pre-commit-config.yaml

# ── PM skill ──────────────────────────────────────────────────────────────────
# claude.ai uploads a skill as a zip with the skill folder at its root
# (codekit-board/SKILL.md), so zip from pm/skills rather than from pm/.

PM_ZIP ?= dist/codekit-board.zip

.PHONY: pm-zip
pm-zip: ## Zip the codekit-board skill for upload to claude.ai (dist/codekit-board.zip)
	@mkdir -p $(dir $(PM_ZIP))
	@rm -f $(PM_ZIP)
	@cd pm/skills && zip -qr $(abspath $(PM_ZIP)) codekit-board -x '*.DS_Store'
	@echo "✓ $(PM_ZIP)"
	@unzip -l $(PM_ZIP) | tail -n +4 | head -n -2 | awk '{print "  " $$4}'

# ── Status ────────────────────────────────────────────────────────────────────

.PHONY: status
status: ## Show per-platform install status and tool availability
	@echo ""
	@echo "── Antigravity IDE Plugin ───────────────────────────────"
	@test -L $(ANTIGRAVITY_PLUGINS)/codekit \
		&& echo "  linked -> $$(readlink $(ANTIGRAVITY_PLUGINS)/codekit)" \
		|| echo "  codekit not linked (run: make antigravity-ide)"
	@echo ""
	@echo "── Antigravity CLI Plugin ───────────────────────────────"
	@command -v agy >/dev/null 2>&1 \
		&& { agy plugin list 2>/dev/null | grep -i codekit || echo "  codekit not installed (run: make antigravity-cli)"; } \
		|| echo "  agy not installed"
	@echo ""
	@echo "── Claude Plugin ────────────────────────────────────────"
	@claude plugin list 2>/dev/null | grep -i codekit || echo "  codekit not installed (run: make claude)"
	@echo ""
	@echo "── Tools ────────────────────────────────────────────────"
	@command -v gh >/dev/null 2>&1 && { gh auth status >/dev/null 2>&1 && echo "  gh: authenticated" || echo "  gh: installed, not authenticated (gh auth login)"; } || echo "  gh: not installed"
	@command -v uv >/dev/null 2>&1 && echo "  uv: installed" || echo "  uv: not installed (curl -LsSf https://astral.sh/uv/install.sh | sh)"
	@out=$$(python3 skills/linear-docs/scripts/linear_docs.py --check 2>/dev/null) \
		&& echo "  $$out" \
		|| echo "  LINEAR_API_KEY: not set or rejected (optional, for linear-docs)"
	@command -v specify >/dev/null 2>&1 && echo "  specify: installed" || echo "  specify: not installed (optional: make speckit)"
	@command -v openspec >/dev/null 2>&1 && echo "  openspec: installed" || echo "  openspec: not installed (optional: make openspec)"
	@echo ""

# ── Cleanup ───────────────────────────────────────────────────────────────────

.PHONY: clean
clean: ## Remove pre-commit cache
	pre-commit clean --config .config/.pre-commit-config.yaml
	@echo "✓ pre-commit cache cleared"
