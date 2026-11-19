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
- **API contract** — when the project publishes an OpenAPI/Swagger spec (or uses springdoc annotations): documented operations that don't exist, documented statuses the code doesn't return, required fields it doesn't enforce, and field names or types that differ between the spec and the JSON.

It covers Java and Kotlin, Spring MVC and WebFlux (annotated controllers and functional routes), is version-aware (Spring Boot 2.x, 3.0–3.1, 3.2+, 4.x), reads the project's global config before judging anything, and follows your team's own conventions when you write them down. Besides the review, this repository has a fast [standalone checker](#quick-check-no-ai-ci-friendly), a [`/validate-api` command](#the-validate-api-command) for branches and pull requests, and [GitHub Actions](#github-actions). See the [changelog](CHANGELOG.md) for what changed in each version.

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

The plugin itself is instructions and reference files only, as the Claude plugin directory requires; the standalone checker and the GitHub Action below live in this repository.

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

[`checker/`](checker) is a standalone checker you run on its own — in a terminal or in CI. It isn't part of the plugin (the review does these checks by reading the code). It needs only Python 3 (standard library), takes about a second on a few hundred files, and flags the defects that can be matched exactly:

| Rule | What it catches |
|---|---|
| QC01–QC02 | No validation provider; `javax` vs `jakarta` validation imports for the Boot version |
| QC03–QC07 | `@RequestBody` without `@Valid`; nested objects/lists that don't cascade; constraints on the wrong type (`@NotBlank` on a `Long`); `@NotNull` on primitives; primitives in request bodies that silently become 0/false |
| QC08–QC12 | `required = false` primitives (500 when absent); `@RequestMapping` without a method; `@PathVariable` names that don't match the URI template; several request bodies; bodies on GET/DELETE |
| QC13–QC14 | Action verbs in GET paths (`GET /orders/{id}/cancel`); date parameters without `@DateTimeFormat` |
| QC15–QC17 | JPA entities as request bodies (mass assignment) or responses; bare `orElseThrow()` giving 500 instead of 404; password limits above BCrypt's 72 bytes |
| QC18–QC19 | Unhandled errors reaching clients as 401 behind a stateless token filter; Kotlin constraints without `@field:` |
| QC20 | Request fields that allow longer strings or larger numbers than the database column they end up in — limits read from Flyway/SQL migrations (in order, including later `ALTER`/`RENAME`), Liquibase XML and `@Column`, including money copied into a narrower column elsewhere |
| QC21–QC24 | WebFlux and functional endpoints: functional handlers that read a constrained body without validating it; `block()` in a WebFlux app; lookups that return an empty `Mono` (or a Kotlin `null`) as 200 instead of 404; exceptions mapped in `@ControllerAdvice` but thrown from functional routes the advice doesn't cover (WebFlux on Spring 5, or advice scoped by package/type) |
| QC25–QC29 | OpenAPI contract drift: documented operations with no handler (and undocumented handlers); documented success statuses the handler doesn't return; documented-required fields the DTO doesn't enforce; property names/types that differ between the spec schema and the DTO's JSON; springdoc `@ApiResponse`/`@Schema(required)` that contradict the code. Reads OpenAPI 3 and Swagger 2, YAML or JSON |
| QC30 | Deletes that reach shared rows: `cascade = ALL`/`REMOVE` on a `@ManyToOne` or `@ManyToMany` removes the type, category or tag other records still use — with `ON DELETE CASCADE` in the schema that silently deletes other users' data, otherwise the delete fails. Found in spring-petclinic-rest, where deleting one owner deletes other owners' pets |
| QC31–QC35 | Patterns confirmed in real projects (spring-petclinic-rest, the RealWorld example): a catch-all `@ExceptionHandler(Exception)` that turns bad JSON, wrong types, 404/405/415 and 403 into 500; Spring Security 5 `antMatchers` that Spring MVC also serves with a trailing slash, letting `/path/` through a broader `permitAll`; `Location` headers that ignore the context path; 204 responses with a body that never arrives; empty lists answered with 404 |

```bash
python3 checker/quick_check.py <project-root>
python3 …/quick_check.py <project-root> --json                    # machine-readable
python3 …/quick_check.py <project-root> --fail-on error --skip QC16  # exit 1 on errors, for CI
python3 …/quick_check.py --list-rules
```

Findings marked `[verify]` are heuristics worth a look rather than certain defects. A clean run says nothing about HTTP semantics, ownership or business rules — that's what the skill's full review is for. Other options: `--diff-base origin/main` (only files changed since the branch left `main`), `--format github` (Actions annotations) and `--format markdown` (a summary table).

## GitHub Actions

Two ready-made workflows in [`examples/workflows/`](examples/workflows) — copy either or both into `.github/workflows/` of your Spring Boot repository.

**Quick check on every PR** — free, no API key, about a second ([`spring-api-quick-check.yml`](examples/workflows/spring-api-quick-check.yml)). This repository is itself a GitHub Action:

```yaml
- uses: actions/checkout@v5
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

- `evals/` holds thirteen test cases — small Spring apps with planted defects and one grader file per expected finding:
  - `full-audit-order-service`, `http-verbs-user-service`, `project-rules-boot2-catalog`: a full audit, an HTTP-verb review, and a Boot 2.7 app with team rules;
  - `boot4-jwt-error-dispatch`, `managed-club-ownership`, `double-accept-transfers`: lessons from a real-app review — errors surfacing as 401 in a stateless JWT setup on Boot 4, writes allowed on clubs the user doesn't manage, and a counter offer that can be paid twice;
  - `kotlin-books-api`, `webflux-shop-api`: Kotlin + Spring MVC, and WebFlux with functional routes;
  - `openapi-drift-orders`: a published OpenAPI spec that has drifted from the code;
  - `warehouse-readonly-traps`, `clinic-method-security`, `webflux-boot27-catalog`: version and proxy traps with decoys — a GET that saves through dirty checking next to a read-only one that doesn't, leftover `javax` constraints and a class-level `@Validated` on Boot 3.2, a `@PreAuthorize` skipped by a self-call next to one that works, and a Boot 2.7 WebFlux app where advice, parameter constraints and ISO dates behave as they did before Spring 6;
  - `recipes-shared-cascade`: deletes that cascade into shared reference data (a cuisine, other authors' recipes in a cookbook), modelled on a bug the skill found in spring-petclinic-rest.
  Every case also checks precision: that no finding makes a materially wrong claim, that working guards are acknowledged, and that latent issues aren't over-rated.
  They live outside the plugin folder, so they aren't shipped to users. Run them with `claude plugin eval plugins/spring-api-validator --eval-dir evals --scaffold --allow-tools Write,Edit,Bash` (real, billed model runs).
- Validate before publishing: `claude plugin validate . --strict`.
- `checker/list_endpoints.py` (standard-library Python 3) prints an endpoint inventory: `python3 checker/list_endpoints.py <project-root>`; `checker/openapi_spec.py <project-root>` lists the operations it reads from OpenAPI/Swagger specs.
- `.github/workflows/ci.yml` runs the unit tests, validates the plugin and marketplace, and runs this repository's own action on an eval app to check its outputs and failure behaviour.
- `tests/test_quick_check.py` (repository root) runs the quick checker against the eval apps and asserts every planted mechanical defect is found and the clean app stays quiet; `tests/test_plugin_folder.py` keeps the plugin folder within the Claude plugin directory's rules (Markdown, JSON, YAML and images only, no `#!` files). Run both with `python3 -m unittest discover tests`.

## License

MIT — see [LICENSE](LICENSE).
