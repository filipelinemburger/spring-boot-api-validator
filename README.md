<img src="plugins/spring-api-validator/assets/icon.png" width="96" alt="" align="right">

# Spring API Validator

A Claude Code plugin (and Agent Skill) that reviews the REST API of a Spring Boot application and reports what is actually broken — not style nits. It reads what each endpoint *does*, then compares that with what the API *claims*:

- **HTTP method semantics** — traces every handler into its services and repositories to classify it (read, create, replace, partial update, delete, action) and flags mismatches: a GET that writes (including hidden JPA dirty-checking writes), a POST that only reads, a PUT that isn't idempotent, a PATCH that wipes fields. Knows the legitimate exceptions (action sub-resources, complex search).
- **Status codes and URIs** — 201 + `Location` on create, 204 on delete, 404 vs 500 for missing resources, plural kebab-case paths.
- **Parameter binding** — path-variable name mismatches, `required = false` primitives, enum and date conversion, `-parameters`, mappings without a method.
- **Bean Validation** — missing `@Valid`, nested and collection elements, constraints on the wrong types, primitives that can never be null, `javax` vs `jakarta`, Kotlin use-site targets, limits vs database columns.
- **Request/response objects** — entity exposure, recursion and lazy loading, mass assignment, Jackson construction and naming, money/date/id types.
- **Errors** — unmapped exceptions, inconsistent error bodies, and where unhandled errors end up (including the stateless-JWT "every error becomes a 401" trap).
- **Ownership and business rules** — every id scoped to the caller, the same rule enforced on every path, double-submission of money-moving actions.

It is version-aware (Spring Boot 2.x, 3.0–3.1, 3.2+, 4.x), reads the project's global config before judging anything, and follows your team's own conventions when you write them down.

## Install

In Claude Code:

```
/plugin marketplace add filipelinemburger/spring-boot-api-validator
/plugin install spring-api-validator@spring-tools
```

Or from a terminal:

```bash
claude plugin marketplace add filipelinemburger/spring-boot-api-validator
claude plugin install spring-api-validator@spring-tools
```

Update later with `/plugin marketplace update spring-tools` (or turn on auto-update for the marketplace in `/plugin`).

## Use

Open a Spring Boot project and ask in plain words — the skill loads on its own:

- "validate the REST API in this project"
- "check whether my endpoints use the right HTTP methods and status codes"
- "review the new ProductController before I open the PR"
- "validate only the endpoints I changed on this branch"

Or call it explicitly: `/spring-api-validator:spring-api-validator [scope]`.

### The `validate-api` command

For a fixed scope, or to review a branch before you open a PR:

```
/spring-api-validator:validate-api                         # the whole API
/spring-api-validator:validate-api OrderController         # one controller (or "POST /orders", a package, a path)
/spring-api-validator:validate-api --diff                  # only what this branch changes vs. the default branch
/spring-api-validator:validate-api --diff origin/develop --errors-only --out api-review.md
/spring-api-validator:validate-api --comment acme/shop/pull/42   # review that PR and post the findings on it
```

In `--diff` mode it reviews every endpoint the change affects — changed controllers, and endpoints that use a changed DTO, service, advice or config — marks pre-existing problems as such, and keeps them out of the counts.

You get a Markdown report: the stack it detected, an endpoint inventory (what each handler really does), findings grouped as **Errors / Warnings / Suggestions** with `file:line`, runtime consequence, fix and confidence, and a "Looks good" list. It only changes code if you ask it to fix the findings, and only runs the app if you ask for a runtime check (local or test instances only).

### Your team's rules

Add `.api-validator.md` at the repository root to describe your conventions (path prefix, error body, which verbs you use, DTO naming…). They take precedence over the generic defaults. A template ships with the skill: [`project-rules-template.md`](plugins/spring-api-validator/skills/spring-api-validator/references/project-rules-template.md).

## Quick check (no AI, CI-friendly)

The plugin ships a standalone checker the skill runs first, and that you can run on its own — in a terminal or in CI. It needs only Python 3 (standard library), takes about a second on a few hundred files, and flags the defects that can be matched exactly:

| Rule | What it catches |
|---|---|
| QC01–QC02 | No validation provider; `javax` vs `jakarta` validation imports for the Boot version |
| QC03–QC07 | `@RequestBody` without `@Valid`; nested objects/lists that don't cascade; constraints on the wrong type (`@NotBlank` on a `Long`); `@NotNull` on primitives; primitives in request bodies that silently become 0/false |
| QC08–QC12 | `required = false` primitives (500 when absent); `@RequestMapping` without a method; `@PathVariable` names that don't match the URI template; several request bodies; bodies on GET/DELETE |
| QC13–QC14 | Action verbs in GET paths (`GET /orders/{id}/cancel`); date parameters without `@DateTimeFormat` |
| QC15–QC17 | JPA entities as request bodies (mass assignment) or responses; bare `orElseThrow()` giving 500 instead of 404; password limits above BCrypt's 72 bytes |
| QC18–QC19 | Unhandled errors reaching clients as 401 behind a stateless token filter; Kotlin constraints without `@field:` |

```bash
python3 plugins/spring-api-validator/skills/spring-api-validator/scripts/quick_check.py <project-root>
python3 …/quick_check.py <project-root> --json                    # machine-readable
python3 …/quick_check.py <project-root> --fail-on error --skip QC16  # exit 1 on errors, for CI
python3 …/quick_check.py --list-rules
```

Findings marked `[verify]` are heuristics worth a look rather than certain defects. A clean run says nothing about HTTP semantics, ownership or business rules — that's what the skill's full review is for. Other options: `--diff-base origin/main` (only files changed since the branch left `main`), `--format github` (Actions annotations) and `--format markdown` (a summary table).

## GitHub Actions

Two ready-made workflows in [`examples/workflows/`](examples/workflows) — copy either or both into `.github/workflows/` of your Spring Boot repository.

**Quick check on every PR** — free, no API key, about a second ([`spring-api-quick-check.yml`](examples/workflows/spring-api-quick-check.yml)). This repository is itself a GitHub Action:

```yaml
- uses: actions/checkout@v4
  with: { fetch-depth: 0 }
- uses: filipelinemburger/spring-boot-api-validator@v0
  with:
    path: .          # folder with pom.xml / build.gradle
    fail-on: error   # error | warning | suggestion | never
    skip: QC16       # optional
```

It checks only the files the PR changes, shows each finding as an annotation on the changed line, writes a table to the job summary, exposes `errors` / `warnings` outputs, and fails the job at the severity you choose.

**Full review by Claude on every PR** ([`spring-api-claude-review.yml`](examples/workflows/spring-api-claude-review.yml)). Uses the official [Claude Code GitHub Action](https://github.com/anthropics/claude-code-action) to install this plugin and run `/spring-api-validator:validate-api --diff … --comment …`: Errors and Warnings become inline review comments on the changed lines, plus one summary comment. It only reports — never approves, pushes or edits. Needs the Claude GitHub App and an `ANTHROPIC_API_KEY` secret, costs one model review per run, and is skipped for drafts and fork PRs (which don't get secrets).

## Using it with other agents

The skill itself is a standard Agent Skill folder — [`plugins/spring-api-validator/skills/spring-api-validator`](plugins/spring-api-validator/skills/spring-api-validator) — so it also works outside the plugin system. For Codex, copy or symlink that folder into `~/.codex/skills/` and call it with `$spring-api-validator`; `agents/openai.yaml` provides its display name there.

## Development

- `plugins/spring-api-validator/evals/` holds six test cases — small Spring apps with planted defects and one grader file per expected finding:
  - `full-audit-order-service`, `http-verbs-user-service`, `project-rules-boot2-catalog`: a full audit, an HTTP-verb review, and a Boot 2.7 app with team rules;
  - `boot4-jwt-error-dispatch`, `managed-club-ownership`, `double-accept-transfers`: lessons from a real-app review — errors surfacing as 401 in a stateless JWT setup on Boot 4, writes allowed on clubs the user doesn't manage, and a counter offer that can be paid twice.
  Every case also checks precision: that each top-severity finding is accurate, that working guards are acknowledged, and that latent issues aren't over-rated.
  Run them with `claude plugin eval plugins/spring-api-validator --scaffold --allow-tools Write,Edit,Bash` (real, billed model runs).
- Validate before publishing: `claude plugin validate . --strict`.
- `scripts/list_endpoints.py` (standard-library Python 3) prints the endpoint inventory the skill starts from: `python3 plugins/spring-api-validator/skills/spring-api-validator/scripts/list_endpoints.py <project-root>`.
- `.github/workflows/ci.yml` runs the unit tests, validates the plugin and marketplace, and runs this repository's own action on an eval app to check its outputs and failure behaviour.
- `tests/test_quick_check.py` runs the quick checker against the eval apps and asserts every planted mechanical defect is found and the clean app stays quiet: `python3 -m unittest discover plugins/spring-api-validator/tests`.

## License

MIT — see [LICENSE](LICENSE).
