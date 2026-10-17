# Secrets and Credentials

**Activation: Always On**

Credential files stay out of the session. Reading one puts its contents into context — where they may be cached, logged, or summarized into a transcript you don't control.

## Do not read

- `.env`, `.env.*`, `.envrc`
- `id_rsa`, `id_ed25519`, `*.pem`, `*.key`, `*.p12`
- `/etc/passwd`, `/etc/shadow`
- `credentials.json`, `service-account*.json`, `*.keystore`
- Anything under `.aws/`, `.ssh/`, `.gnupg/`

This includes indirect reads: `grep`, `cat`, `head`, `sed`, and file-search tools all pull contents into context just as much as opening the file does.

## Do not write

Never write to `.env*`. Secrets are managed outside AI sessions — by the user, in their secret manager or shell profile.

If a task genuinely needs an env var, ask the user to set it themselves and tell them the exact variable name. Suggest they run it as `! export FOO=...` so it lands in their shell, not in a file you wrote.

## When you need to know what's configured

Read the *keys*, not the values:

```bash
# Safe — names only
grep -o '^[A-Z_]*=' .env.example
cut -d= -f1 .env 2>/dev/null
```

Prefer `.env.example` — it exists precisely so tools can learn the shape of the config without the secrets. If it's missing or stale, that's worth flagging to the user as a docs gap.

## If a secret lands in context anyway

Say so plainly and immediately. Don't repeat the value, don't include it in a summary or commit message, and recommend the user rotate it. A leaked credential that nobody knows about is worse than one that's been reported.
