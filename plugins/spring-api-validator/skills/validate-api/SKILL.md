---
name: validate-api
description: Run the Spring API validator on a chosen scope — the whole API, one controller or endpoint, or only what a branch or pull request changes — and optionally post the findings as pull-request review comments. Invoked explicitly as /spring-api-validator:validate-api with arguments; used by the GitHub Action workflow for PR reviews.
argument-hint: "[--diff [base]] [--comment owner/repo/pull/N] [--errors-only] [--out file] [controller, endpoint or path]"
disable-model-invocation: true
---

# validate-api

A thin entry point with arguments. The review itself is done by the main skill of this plugin, which lives next to this one: `../spring-api-validator/SKILL.md` relative to this skill's base directory. Read that file now and follow its workflow; its `references/` and `scripts/` paths are relative to its own folder.

Arguments: `$ARGUMENTS`

## 1. Parse the arguments

| Argument | Meaning |
|---|---|
| *(none)* | The whole API of the project in the current directory. |
| `--diff [base]` | Only what the current branch changes compared with `base` (default: the remote's default branch, e.g. `origin/main`; find it with `git symbolic-ref refs/remotes/origin/HEAD`). Include uncommitted changes. |
| `--comment owner/repo/pull/N` | Post the findings on that pull request (see step 4). Implies `--diff` against the PR's base branch if no other scope is given. |
| `--errors-only` | Report Errors only; skip Warnings and Suggestions. |
| `--out <file>` | Also write the report to this file. |
| anything else | A scope: a controller (`OrderController`), an endpoint (`POST /orders`), a package or a path. |

If something is ambiguous (two controllers match), pick the most likely one and say so in the report rather than stopping to ask — this command often runs unattended in CI.

## 2. Settle the scope for a diff

With `--diff`:

1. `git merge-base <base> HEAD`, then `git diff --name-only <merge-base>` plus untracked files (`git ls-files --others --exclude-standard`) give the changed files.
2. In scope: every endpoint whose controller changed, plus every endpoint that reads or returns a changed DTO, calls a changed service/repository method, or is affected by a changed advice, security config, Jackson/MVC config or `application*.yml`. Use `scripts/list_endpoints.py` and a search for the changed types to find them.
3. Run the quick check limited to the diff: `python3 <main-skill-dir>/scripts/quick_check.py <project-root> --diff-base <base>`. Its findings are leads; confirm each.
4. Review the endpoints in scope with the full workflow — the main skill's checklist (plus `kotlin.md`/`webflux.md` when they apply), opening detail files to settle specific findings. A diff is a smaller scope, not a lighter check. Look at the rest of the API only to judge consistency (a new endpoint that breaks an existing convention).
5. For every new or changed write endpoint, write down which authorization check it performs (e.g. `requireOwned` + `requireInSave`) and which check the existing write endpoints on the same kind of resource perform (e.g. `requireManagedClub`). A new endpoint with a weaker check than its siblings is an Error even when the code compiles and the save-level ownership is right. New endpoints are where these gaps appear.

If nothing in the diff touches the API (no controllers, DTOs, services they call, or web/security config), say so in one line and stop.

## 3. Report

Use the main skill's report format, with **Scope** naming the base and the number of changed files. With `--errors-only`, keep only the Errors section and the inventory rows that have an Error. In a diff review, mark findings that existed before this change as "pre-existing" (check with `git blame` or by comparing with the base) and keep them out of the counts in the summary — a pull request shouldn't be blamed for old code, but the reader should know about it.

Write the report to `--out` if given, and always show it in the final message.

## 4. Post to the pull request (`--comment`)

Only with `--comment`, and only findings this change introduces (not pre-existing ones):

- **Inline comments**: if the tool `mcp__github_inline_comment__create_inline_comment` is available (it is in the GitHub Action workflow), post one comment per finding on the changed line it concerns: the severity and title on the first line, then the problem, the fix and the confidence, in two to five short lines. Group a repeated mistake into one comment on its first occurrence that lists the other lines. Post Errors and Warnings inline; leave Suggestions for the summary.
  - Finish the whole review and write the report before posting anything, so every comment reflects the final findings.
  - Grouping is for comments only: a Warning mentioned inside an Error's comment is still a Warning. Count every finding at its own severity in the summary and list it in its own section there.
  - Comments can't be edited or deleted afterwards, so get the line right first: re-read the file in the PR's version and confirm the target line contains the code the comment is about (for a multi-line declaration, use the line with the annotation or call in question). Never post a second comment to correct a first one; if a comment did land on the wrong line, say so once in the summary comment.
- **Summary comment**: post the report summary (counts, the inventory rows in scope, the Suggestions and the "Looks good" list) as one top-level comment with `gh pr comment <N> --repo <owner/repo> --body-file <file>`. If `gh` isn't available or fails, append the full report to `$GITHUB_STEP_SUMMARY` when that variable is set, and say where the report went.
- If the PR has no findings, post a single short summary comment saying what was checked.

Never approve, request changes, merge, push or edit code from this command — it reports only.
