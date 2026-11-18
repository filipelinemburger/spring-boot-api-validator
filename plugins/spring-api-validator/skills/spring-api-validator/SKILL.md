---
name: spring-api-validator
description: Validate the REST API of a Spring Boot (Java or Kotlin) application — controller and code structure, endpoint paths, HTTP method semantics (GET reads, POST creates, PUT replaces, PATCH partially updates, DELETE removes), request/response DTO structure, Bean Validation, parameter binding and Java type behaviour, Jackson serialization, status codes and error handling, checked against the project's own API rules when it has them. Use this whenever the user asks to validate, review, audit, lint or sanity-check a REST API, controllers, endpoints, routes, DTOs or request/response objects in a Spring / Spring Boot / Spring MVC / WebFlux project, asks whether endpoints use the right HTTP verbs or status codes, or wants a new or changed endpoint checked before merging — even if they don't say "validate" or name the skill.
---

# Spring API Validator

Find real defects in a Spring REST API: things that silently don't work (validation that never runs, parameters that fail to bind, a GET that writes to the database) first, contract and convention problems second. A good run produces a report a developer can act on line by line, with no false alarms they have to argue with.

The core idea: **read what the code actually does, then compare it with what the API claims.** An annotation, a verb or a DTO field is a claim; the build file, global config, service code and Java/Jackson/Spring runtime behaviour decide whether the claim holds.

## Workflow

### 1. Settle the scope

Work out from the request what to validate: the whole API, one controller, one endpoint, or the current change (`git diff` / branch vs main). For a change, validate the changed endpoints fully and only glance at the rest for consistency; `quick_check.py --diff-base <base>` limits the quick check to the changed files. Say the scope in the report. (When the user runs `/spring-api-validator:validate-api` with arguments, that skill settles the scope and output first and then hands over to this workflow.)

### 2. Read the stack before judging anything

Many rules depend on versions and global settings, and getting them wrong is the main source of false positives. Before checking endpoints, collect:

- **Build file** (`pom.xml`, `build.gradle(.kts)`): Spring Boot version, Java/Kotlin version, `spring-boot-starter-validation` present, `spring-boot-starter-parent` or the Spring Boot Gradle plugin (both enable the `-parameters` compiler flag), Lombok, springdoc/swagger, Spring Data, WebMVC vs WebFlux.
- **Validation namespace**: `javax.validation` (Boot 2) vs `jakarta.validation` (Boot 3). An import from the wrong namespace compiles if that jar is on the classpath but is silently ignored.
- **Global config** (`application.yml/properties`, `@Configuration` classes, `Jackson2ObjectMapperBuilderCustomizer`, `WebMvcConfigurer`): `server.servlet.context-path`, `spring.mvc.servlet.path`, `spring.jackson.*` (naming strategy, inclusion, date format, fail-on-unknown-properties), `spring.mvc.problemdetails.enabled`, `spring.jpa.open-in-view`, path prefixes added via `configurePathMatch`.
- **Existing conventions**: `@RestControllerAdvice` classes, error-response classes, a base response envelope, how other controllers name paths and return statuses. Consistency with the codebase beats generic best practice.

`references/versions.md` lists what changes between Boot 2.x, 3.0–3.1, 3.2+ and 4.x.

### 3. Load the project's own rules

Look for `.api-validator.md` at the repository root (template: `references/project-rules-template.md`), and API conventions in `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md` or `docs/`. Project rules override the generic guidance in this skill: if the team mandates `POST /orders/{id}/cancel`, or a response envelope, don't flag it. When a project rule and a real runtime defect conflict (e.g. a mandated pattern that makes validation never run), report the defect and mention the rule.

### 4. Build the endpoint inventory and run the quick check

Run the two bundled scripts first (Python 3, standard library only; each takes about a second):

```bash
python3 <skill-dir>/scripts/list_endpoints.py <project-root>
python3 <skill-dir>/scripts/quick_check.py <project-root>
```

`list_endpoints.py` prints every mapping it can find: HTTP method, full path (class + method mapping, plus context path if it finds one), handler and `file:line`. Treat it as a map, not as truth — confirm each in-scope endpoint by reading the controller, and resolve paths built from constants yourself. Then, for each endpoint in scope, note: parameters (path/query/header/body) with their Java types, the request DTO, the return type, the status it returns, and the service/repository calls it makes.

`quick_check.py` flags the mechanical defects that can be matched exactly — missing `@Valid`, non-cascading nested validation, constraints on the wrong type, `required = false` primitives, `@RequestMapping` without a method, path-variable name mismatches, the wrong validation namespace, entities as bodies or responses, request-body primitives, bare `orElseThrow()`, BCrypt limits above 72, the stateless-filter error-dispatch trap and more (`--list-rules`). Use it as a list of leads: open each finding, confirm it, and judge its real severity in context — `[verify]` findings are heuristics (an invariant lookup that can't miss is not a 404 bug). It doesn't follow calls or know intent, so a clean run says nothing about HTTP semantics, ownership, business rules or concurrency; those are still yours to check in step 5. Don't paste its output into the report; fold confirmed findings into your own, one per root cause.

### 5. Check each endpoint

These facts are the ones reviews most often get wrong from memory. Check them against the project's versions before writing any finding that touches them:

- **Spring Framework 6.1+ (Boot 3.2+)** validates constraint annotations on `@PathVariable`/`@RequestParam`/`@RequestHeader` by itself — no class-level `@Validated` is needed, and adding one switches to the AOP path (`ConstraintViolationException`, a 500 unless handled). Before 6.1, those constraints need class-level `@Validated`.
- `spring-boot-starter-parent` and the Spring Boot Gradle plugin turn on `-parameters`; unnamed `@PathVariable`s only break without them (and only on 6.1+).
- Spring Data 3.x `deleteById` ignores a missing id; 2.x throws `EmptyResultDataAccessException`.
- Spring MVC answers HEAD by running the GET handler, so a GET's side effects happen on HEAD too.
- MockMvc doesn't perform error dispatches; anything about `/error` behaviour has to be confirmed against a running server.

Go through these areas, reading the reference file for an area when an endpoint touches it. A small scope (one controller, a diff) means fewer endpoints, not a shallower check: still read the reference for every area the endpoints in scope touch. The references explain *why* each rule matters and how Spring behaves at runtime, which is what lets you tell a real bug from a style preference.

| Area | What to check | Reference |
|---|---|---|
| HTTP method semantics | Classify what the handler really does (read / create / replace / partial update / delete / action) by tracing into services and repositories, then compare with the verb. Includes status codes per verb and URI design. | `references/http-methods.md` |
| Parameters & binding | `@PathVariable` / `@RequestParam` / `@RequestHeader` names and types, `required`/`defaultValue`, primitives, enums, dates, `-parameters`, mappings without a method, ambiguous mappings. | `references/parameters.md` |
| Bean Validation | `@Valid` placement, nested and collection validation, constraint/type compatibility, primitives, `javax` vs `jakarta`, groups for create vs update, Kotlin use-site targets. | `references/validation.md` |
| Request/response objects | DTO vs entity, Jackson construction and naming, Lombok effects, money/dates/ids/enums, mass assignment, leaked fields. | `references/dto-serialization.md` |
| Responses & errors | Return types, `ResponseEntity`, `Optional`/`null` returns, exceptions that become 500s, `@RestControllerAdvice`, error body consistency, pagination. | `references/responses-errors.md` |
| Code structure | Layering, controller responsibilities, injection, security annotations consistency. | `references/structure.md` |

Two checks are app-wide, so do them once yourself before going endpoint by endpoint: where unhandled exceptions end up (advice coverage, `/error`, security on the error dispatch, and how the client reacts to the resulting status — see `responses-errors.md`), and how ownership is enforced (see `structure.md`). Their answers change the severity of many per-endpoint findings.

**Large APIs** (roughly 30+ endpoints): if you can run subagents, split the controllers into groups of related features and review the groups in parallel. Give each reviewer the stack facts and the app-wide answers you already established, point it at this skill's references, and ask for inventory rows, findings with `file:line` and quoted code, and a "looks good" list — not a report. Then re-open the code for every Error yourself before it goes into the report; merge findings that share a root cause across groups.

The HTTP method check needs the most care. Don't judge a handler by its name: `getOrderDetails` may write to the database through JPA dirty checking, and `processOrder` may be a pure read. Follow the call chain until you know whether state changes (repository `save`/`delete`/`@Modifying` queries, setters on managed entities inside `@Transactional`, messages sent, emails, external calls).

### 6. Optional: confirm at runtime

Static reading is the default. If the user asks for it, or a finding can only be settled by running the code (e.g. whether a constructor deserializes), follow `references/runtime-check.md`: prefer a `@WebMvcTest`/MockMvc test, or start the app locally against a local/test profile and probe it with `curl`. Never send requests to anything but a local or test instance, and only send write requests (POST/PUT/PATCH/DELETE) to local data.

### 7. Report

Verify every finding against the code before writing it: re-open the line, confirm the version/config it depends on. When you describe a consequence ("`{}` wipes the product"), trace that exact request through the handler: if an earlier failure (an NPE, a binding error) stops it first, describe the request that really reaches the damage instead. Keep every count consistent with what it counts — in the summary, the inventory and "Looks good". Check that each suggested fix works where it runs: inside a `@Transactional` method, state you change and then throw away with an exception is rolled back, so "mark the offer rejected, then throw" doesn't persist the rejection. When existing guards already handle a case (a sequential repeat rejected with 409, a status check), say so in "Looks good" so the reader knows which risks remain and which don't. If something depends on runtime config you couldn't see, mark it "likely" and say what would confirm it. Only report what you checked.

Use this structure:

```markdown
# API validation: <app or scope>

**Scope:** <what was checked> · **Stack:** Spring Boot X.Y, Java NN, <MVC/WebFlux>, <validation/jackson notes> · **Project rules:** <file used, or "none found">

## Summary
<2–4 sentences: overall health, the most important problems, counts by severity>

## Endpoint inventory
| Method | Path | Handler | Does | Verdict |
|---|---|---|---|---|
| GET | /api/orders/{id} | OrderController#get (OrderController.java:42) | read | ⚠ 2 issues |

("Does" is the classified behaviour: read, create, replace, partial update, delete, action.)

## Findings

### Errors — broken or unsafe behaviour today
1. **<short title>** — `path/File.java:line` · `GET /orders/{id}/cancel`
   - **Problem:** what is wrong and what happens at runtime (status code, exception, data effect).
   - **Fix:** the concrete change, with a short code snippet when it helps.
   - **Rule:** the rule in plain words ("a GET must not change state"), or the project rule it breaks quoted from the team's rules file. Don't cite this skill's reference file names — the reader of the report has never seen them. (Confidence: confirmed | likely — and why)

### Warnings — contract, semantics or consistency problems
...

### Suggestions — conventions and improvements
...

## Looks good
<brief list of things checked that are correct, so the reader knows they were covered — e.g. "action endpoint POST /orders/{id}/refunds returns 201 + Location">
```

"Looks good" is a claim like any finding, so it needs the same evidence. For ownership in particular, name the exact check each write endpoint performs and compare it with its siblings: "`replace` checks `requireOwned` + `requireInSave`" is not the same as "`hire` checks `requireManagedClub`", and when sibling writes use the narrower check, the broader one is a finding, not something that looks good.

Severity guide:
- **Error**: wrong behaviour now — validation that never runs, a binding that throws 500, a safe verb with side effects, data loss (PUT/PATCH nulling fields), exposed secrets, a handler matching every HTTP method.
- **Warning**: the API works but breaks its contract or HTTP semantics — wrong verb for the operation, wrong status code, entity exposure, inconsistent error bodies, missing 404 handling.
- **Suggestion**: naming, path style, documentation, consistency polish.

Rate by what happens today, not what could happen: a defect no current code path reaches (a recursive `hashCode` nothing calls, a constraint on a field no endpoint binds) is a Warning at most, with the trigger named.

Keep findings specific: one finding per root cause, grouped when the same mistake repeats ("`@Valid` missing on 4 handlers: …"). Don't pad the report with generic advice that doesn't point at a line of code. If the user asked to fix things, apply fixes only after the report, keeping each fix minimal and consistent with the codebase, and re-check the changed endpoints.
