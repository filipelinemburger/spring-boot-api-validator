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

You get a Markdown report: the stack it detected, an endpoint inventory (what each handler really does), findings grouped as **Errors / Warnings / Suggestions** with `file:line`, runtime consequence, fix and confidence, and a "Looks good" list. It only changes code if you ask it to fix the findings, and only runs the app if you ask for a runtime check (local or test instances only).

### Your team's rules

Add `.api-validator.md` at the repository root to describe your conventions (path prefix, error body, which verbs you use, DTO naming…). They take precedence over the generic defaults. A template ships with the skill: [`project-rules-template.md`](plugins/spring-api-validator/skills/spring-api-validator/references/project-rules-template.md).

## Using it with other agents

The skill itself is a standard Agent Skill folder — [`plugins/spring-api-validator/skills/spring-api-validator`](plugins/spring-api-validator/skills/spring-api-validator) — so it also works outside the plugin system. For Codex, copy or symlink that folder into `~/.codex/skills/` and call it with `$spring-api-validator`; `agents/openai.yaml` provides its display name there.

## Development

- `plugins/spring-api-validator/evals/` holds the test cases: three small Spring apps with planted defects (a full audit, an HTTP-verb review, and a Boot 2.7 app with team rules) and one grader file per expected finding. Run them with `claude plugin eval plugins/spring-api-validator --scaffold --allow-tools Write,Edit,Bash` (real, billed model runs).
- Validate before publishing: `claude plugin validate . --strict`.
- `scripts/list_endpoints.py` (standard-library Python 3) prints the endpoint inventory the skill starts from: `python3 plugins/spring-api-validator/skills/spring-api-validator/scripts/list_endpoints.py <project-root>`.

## License

MIT — see [LICENSE](LICENSE).
