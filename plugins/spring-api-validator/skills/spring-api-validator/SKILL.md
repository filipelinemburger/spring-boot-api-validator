---
name: spring-api-validator
description: Validate the REST API of a Spring Boot (Java or Kotlin) application — controller and code structure, endpoint paths, HTTP method semantics (GET reads, POST creates, PUT replaces, PATCH partially updates, DELETE removes), request/response DTO structure, Bean Validation, parameter binding and Java type behaviour, Jackson serialization, status codes and error handling, checked against the project's own API rules when it has them. Use this whenever the user asks to validate, review, audit, lint or sanity-check a REST API, controllers, endpoints, routes, DTOs or request/response objects in a Spring / Spring Boot / Spring MVC / WebFlux project, asks whether endpoints use the right HTTP verbs or status codes, or wants a new or changed endpoint checked before merging — even if they don't say "validate" or name the skill.
---

# Spring API Validator

Find real defects in a Spring REST API — things that silently don't work (validation that never runs, parameters that fail to bind, a GET that writes) first, contract and convention problems second — and report them so a developer can act line by line, with no false alarms. **Read what the code actually does, then compare it with what the API claims**: annotations, verbs and DTO fields are claims; the build file, global config, service code and Spring/Jackson/Kotlin runtime behaviour decide whether they hold.

## Workflow

1. **Scope.** The whole API, a controller, an endpoint, or a change (branch vs base: `git diff --name-only $(git merge-base <base> HEAD)` plus untracked files). For a change, review affected endpoints fully and look at the rest only for consistency. (`/spring-api-validator:validate-api` settles scope and output, then hands over here.)

2. **Stack and config, before judging anything.** From the build file: Spring Boot version, MVC vs WebFlux, Java/Kotlin, validation starter, Boot parent or Gradle plugin (`-parameters`), Lombok, Spring Data. Validation namespace (`javax` on Boot 2, `jakarta` on 3+). Global config: context/base path, `spring.jackson.*`, `spring.mvc.problemdetails.enabled`, `open-in-view`, path prefixes. Existing conventions: advice classes, error body, response envelope, path style — consistency with the codebase beats generic advice.

3. **Project rules.** `.api-validator.md` at the repo root (template: `references/project-rules-template.md`), or API conventions in `CLAUDE.md`/`AGENTS.md`/`CONTRIBUTING.md`/`docs/`. They override the generic guidance; when one conflicts with a real runtime defect, report the defect and mention the rule.

4. **Inventory and quick check.** If this skill's folder has a `scripts/` directory (Python 3, standard library, about a second each):
   ```bash
   python3 <skill-dir>/scripts/list_endpoints.py <project-root>
   python3 <skill-dir>/scripts/quick_check.py <project-root>    # add --diff-base <base> for a change
   ```
   The inventory lists annotated and functional endpoints with `file:line`; confirm each in-scope one and resolve constants or nested prefixes yourself. The quick check flags mechanical defects (`--list-rules`); treat them as leads to confirm, judge severity in context (`[verify]` = heuristic), and fold confirmed ones into your findings. A clean quick check says nothing about HTTP semantics, ownership, business rules or concurrency.

   Without `scripts/` (some editions ship without them), build the inventory by searching the sources: `@(Get|Post|Put|Patch|Delete|Request)Mapping` with the class-level prefix, `RouterFunction`/`route()`/`coRouter {` builders and their nested `path(...)`/`nest(...)` prefixes, plus `server.servlet.context-path`/`spring.webflux.base-path`. Then do the mechanical checks yourself as part of step 5 — every one is a checklist line: `@Valid` on bodies and nested types, constraint/type mismatches, primitives (`@NotNull` on them, `required = false`, in bodies), mappings without a method, path-variable names, `javax` vs `jakarta`, entities as bodies, bare `orElseThrow()`, BCrypt limits, `@field:` in Kotlin, request limits vs migration/`@Column` sizes, `block()` in WebFlux, and — when there's a spec — each documented operation, status, required field and property name against the code.

5. **Check each endpoint.** Read `references/checklist.md` — every rule in one line with its runtime effect and default severity — plus `references/kotlin.md` for Kotlin sources, `references/webflux.md` for WebFlux or functional routes, and `references/openapi.md` when the project publishes an OpenAPI/Swagger spec or uses springdoc annotations (then the spec is part of what the API claims: compare it with the code, endpoint by endpoint). Open the detail files the checklist points to (`http-methods.md`, `parameters.md`, `validation.md`, `dto-serialization.md`, `responses-errors.md`, `structure.md`, `versions.md`) only to settle a specific finding — when you're unsure of the runtime behaviour, the severity or the fix. A small scope means fewer endpoints, not a shallower check.

   Trace each handler into its services and repositories before judging the verb: `getOrderDetails` may write through JPA dirty checking, `processOrder` may only read. Do two checks once for the whole app first, because they change many severities: where unhandled exceptions end up (advice coverage, `/error`, security on the error dispatch, how the client reacts to the status) and how ownership is enforced (every id scoped to the caller; writes compared with their siblings' checks).

   **Facts reviews most often get wrong from memory** — check them against the project's versions before writing a finding that depends on them:
   - Spring 6.1+ (Boot 3.2+) validates constraints on `@PathVariable`/`@RequestParam`/`@RequestHeader` by itself; no class-level `@Validated` needed, and adding one switches to the AOP path (`ConstraintViolationException`, 500 unless handled). Before 6.1 they need class-level `@Validated`.
   - The Boot Maven parent and Gradle plugin turn on `-parameters`; unnamed `@PathVariable`s only break without them, and only on 6.1+.
   - Spring Data 3.x `deleteById` ignores a missing id; 2.x throws `EmptyResultDataAccessException`.
   - HEAD runs the GET handler, so a GET's side effects happen on HEAD too.
   - Global `@ControllerAdvice` also covers functional routes in WebFlux since Spring 6.0 and in WebMvc.fn since 5.3 (not on WebFlux 5.x, and never for advice scoped by package/type/annotation). Functional handlers never get Bean Validation on their bodies.
   - MockMvc doesn't perform error dispatches; `/error` behaviour must be confirmed against a running server.
   - `ResponseStatusException` gives a ProblemDetail body only with `spring.mvc.problemdetails.enabled` or a matching advice; otherwise Boot's `/error` body, without the reason by default.

   **Large APIs** (30+ endpoints): if you can run subagents, split controllers into feature groups and review them in parallel. Give each the stack facts, the app-wide answers and this skill's checklist; ask for inventory rows and findings with `file:line` and quoted code, not a report. Re-open the code for every Error yourself before it goes into the report.

6. **Runtime check (optional).** Only if asked, or when a finding can only be settled by running code: follow `references/runtime-check.md`. Local or test instances only; write requests only against local data.

7. **Report.** Verify every finding before writing it: re-open the line and confirm the version/config it depends on. Describe consequences for the request that actually reaches the damage (an earlier NPE may stop `{}` first). Check each fix works where it runs — a change followed by an exception inside `@Transactional` is rolled back; a suggested exception reaches the client in the API's format only if the project's advice handles it. State runtime mechanics only as far as you know them: when the verdict is certain but a detail isn't, give the verdict and leave the detail out — but first look up what the code can tell you (the project's advice says which status a database error or custom exception becomes). Mark findings that depend on unseen runtime config "likely" and say what would confirm them.

## Report format

```markdown
# API validation: <app or scope>

**Scope:** … · **Stack:** Spring Boot X.Y, Java/Kotlin NN, MVC/WebFlux, notes · **Project rules:** <file, or "none found">

## Summary
<2–4 sentences: overall health, the top problems, counts by severity>

## Endpoint inventory
| Method | Path | Handler (file:line) | Does | Verdict |
|---|---|---|---|---|

## Findings
### Errors — broken or unsafe today
1. **<title>** — `File.java:line` · `GET /path`
   - **Problem:** what's wrong and what happens at runtime (status, exception, data effect).
   - **Fix:** the change; a short snippet only when the fix isn't obvious.
   - **Rule:** the rule in plain words or the team rule it breaks (never this skill's file names). Confidence: confirmed | likely — why.
### Warnings — contract, semantics or consistency
### Suggestions — conventions and polish

## Looks good
<up to 6 bullets of things checked and correct, with evidence>
```

**Keep it tight**: Problem and Fix one or two sentences each; one finding per root cause, grouping repeats ("`@Valid` missing on 4 handlers: …"); inventory rows only for endpoints in scope; no generic advice that doesn't point at a line; don't repeat findings in the summary beyond counts and the top two or three. "Does" in the inventory is the classified behaviour (read, create, replace, partial update, delete, action). Keep every count consistent with what it counts, and count each finding at its own severity.

**Severity.** Error: wrong behaviour now — validation that never runs, a binding that throws 500, a safe verb with side effects, data loss, exposed secrets, a handler answering every verb. Warning: works but breaks its contract — wrong verb or status, entity exposure, inconsistent errors, missing 404. Suggestion: naming, style, polish. Rate by what happens today: a defect no current path reaches (a recursive `hashCode` nothing calls) is a Warning at most, with the trigger named.

**"Looks good" is a claim too.** Give evidence, and acknowledge guards that already work (a sequential repeat rejected with 409) so the reader knows which risks remain. For ownership, name each write's exact check: when sibling writes use a narrower check (`requireManagedClub` vs `requireOwned` + `requireInSave`), the broader one is a finding.

If the user asked for fixes, apply them only after the report, minimal and consistent with the codebase, and re-check the changed endpoints.
