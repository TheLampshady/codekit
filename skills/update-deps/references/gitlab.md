# GitLab

Through the `glab` CLI, run from the repo root, so the issue lands in the project the `origin` remote points at.

1. `glab issue list --search "<title>" --in title --output json`. If an open issue with the same title exists, reuse it.
2. Otherwise create it, with the description from stdin:
   ```bash
   glab issue create --title "<title>" --description-file - --yes <<'EOF'
   <description>
   EOF
   ```
3. If the branch name starts with an issue number (`123-add-login`) that `glab issue view <n> --output json` finds, add `--linked-issues <n>`, which links the two as related.

The new issue's reference is `#<iid>` from the create output.
