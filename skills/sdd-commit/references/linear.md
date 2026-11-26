# Linear

## Branch

A ticket identifier (`[A-Za-z][A-Za-z0-9]+-\d+`) in the branch name, uppercased, e.g. `user/eng-123-title` → `ENG-123`. Version numbers and dates match the same pattern (`feature/upgrade-node-20` → `NODE-20`), so keep it only if the part before the `-` is the `git config codekit.team` key or, with no team key set, if the Linear MCP's `get_issue` finds it. If Linear can't be reached, keep it and say it's unchecked.

## Link

The issue's `url` from `get_issue` (`fields: ["url"]`, or reuse the call that checked the ID), without the title slug after the ID: `https://linear.app/<workspace>/issue/ENG-123`.
