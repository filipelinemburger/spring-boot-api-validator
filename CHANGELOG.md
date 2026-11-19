# Changelog

All notable changes to the spring-api-validator plugin. Versions follow `plugin.json`; the GitHub Action is published under matching `v0.x.y` tags, and `v0` always points to the latest 0.x release.

## 0.11.1 — 2026-11-19
### Fixed
Precision sweep of the checker over 13 public Spring Boot projects (about 1,370 Java/Kotlin files, Boot 2.0–4.1, Java and Kotlin, MVC and WebFlux, single- and multi-module; no crashes, 2.6 s on the largest). Before: 95 findings, 11 false. After: 91, none known false.
- A class annotation with braces (`@JsonIgnoreProperties({...})`, `@Table(uniqueConstraints = {...})`) hid the annotations above it, so some `@Entity` classes went unrecognised. Fixing it surfaced 7 real findings that had been missed.
- An entity bound as a request body is QC15's finding; its own associations are no longer treated as request DTOs (false QC04/QC06/QC07).
- QC06 skips entities; QC07 rates a missing `boolean` as a Suggestion (false is usually the intended default) and numbers as Warnings.
- QC14 no longer flags `Instant` parameters: Spring parses ISO-8601 instants on every version.
- QC16 skips `orElseThrow()` on an `Optional` that was checked with `isPresent()` first.
- QC17 skips login-style bodies (nothing is encoded); QC20 skips password fields (stored as a hash).
- QC03 on a partial update (PATCH) explains how to validate without requiring every `@NotNull` field.

## 0.11.0 — 2026-11-19
### Added
- Quick-check rules from defects confirmed in real open-source projects, each checked to fire there and stay quiet on the other projects and all test apps:
  - **QC31 catch-all-handler-500** (Error): `@ExceptionHandler(Exception/Throwable/RuntimeException)` in an advice that doesn't extend `ResponseEntityExceptionHandler`, so malformed JSON, wrong parameter types, 404/405/415 and `@PreAuthorize` denials become 500 (spring-petclinic-rest).
  - **QC32 ant-matcher-trailing-slash** (Error, verify): on Boot 2.x, a restrictive `antMatchers("/x")` misses `/x/`, which Spring MVC serves and a broader `permitAll` then lets through (RealWorld: anonymous `GET /articles/feed/`).
  - **QC33 location-without-context-path**, **QC34 no-content-with-body**, **QC35 empty-collection-404** (Warnings, spring-petclinic-rest).
- The skill's checklist covers 204-with-body, context-path `Location` headers and the Spring Security 5 trailing-slash gap.

## 0.10.0 — 2026-11-19
### Added
- Quick-check rule **QC30 cascade-to-shared-entity**: `cascade = ALL`/`REMOVE` on a `@ManyToOne` or `@ManyToMany` (Java and Kotlin), an Error when something in the code deletes those entities. Removing one row then removes the shared row it points to — with `ON DELETE CASCADE` in the schema, other users' data goes with it.
- The skill's checklist and `structure.md` follow what a DELETE really removes through the mappings and the DDL.
- Test app `recipes-shared-cascade`.
- Measured on three real open-source projects (spring-petclinic-rest, the RealWorld Java and Kotlin/WebFlux examples), every finding checked against the code: no false findings either way; the skill mis-ranked 1 finding against 7 without it, and alone found the most severe bug — in spring-petclinic-rest, `Pet.type` is `cascade = ALL`, so deleting an owner deletes other owners' pets on the default H2 schema.
### Fixed
- The checker closes the files it reads.

## 0.9.1 — 2026-11-18
### Fixed
- Dates: Spring falls back to ISO parsing for `java.time` parameters since **6.0** (Boot 3.0), not 6.1. The skill and the checker's QC14 now say so (QC14 is a Suggestion from Boot 3.0).
- The checker's QC20 no longer flags a string whose `@Pattern` already bounds its length (`[A-Z]{3}` into `VARCHAR(3)`).
### Added
- The skill knows that on Spring 6.1+ a constrained parameter next to `@Valid @RequestBody` makes body errors arrive as `HandlerMethodValidationException` instead of `MethodArgumentNotValidException`.
- Three harder test apps: `warehouse-readonly-traps`, `clinic-method-security`, `webflux-boot27-catalog`, with decoys that punish false alarms. Measured with and without the skill: both found every planted defect (17/17 each); the round's value was the two corrections above.

## 0.9.0 — 2026-11-18
### Changed
- **One edition.** The quick-check scripts moved out of the plugin to `checker/` at the repository root, so the plugin on `main` is what the Claude plugin directory accepts (Markdown, JSON, YAML and the icon only). The skill and `/validate-api` build the inventory and do the mechanical checks by reading the code — measured in 0.8.0 at the same accuracy and cost as with the scripts.
- The GitHub Action runs `checker/quick_check.py`; its inputs and outputs are unchanged. Run the checker by hand with `python3 checker/quick_check.py <project-root>`.
- Plugin and marketplace descriptions no longer mention the checker; the plugin README says what the plugin runs and sends without it.
### Removed
- The directory-edition build (`tools/`, `directory/`), its CI job and the `directory` branch: the directory tracks `main` instead.
### Added
- `tests/test_plugin_folder.py` keeps the plugin folder within the directory's rules.

## 0.8.0 — 2026-11-18
### Added
- **Directory edition** for the Claude plugin directory, which accepts no bundled scripts from unverified organizations: `tools/build_directory_edition.py` builds the plugin without `scripts/`, with its own README (`directory/README.md`) and a description that doesn't claim the checker, and checks every file against the directory's rules (allowed types, no `#!`, UTF-8, valid JSON, size). CI rebuilds it on every push to `main` and publishes it to the `directory` branch, which the directory tracks.
- Unit tests for the build (`tests/test_directory_edition.py`).
### Changed
- The skill and the `/validate-api` command work without `scripts/`: they then build the endpoint inventory by searching for mappings and functional routes, and do the quick check's mechanical checks (and the OpenAPI comparisons) by reading the code. With `scripts/` present — the marketplace install, Codex, the GitHub Action — nothing changes.
- Measured on three test apps (order service, WebFlux shop, OpenAPI drift): the script-free edition scored 38/38, the same as the full edition, at about the same cost (92k tokens, 161 s on average vs 92k, 158 s); without the skill, 34/38.

## 0.7.2 — 2026-11-18
### Changed
- The plugin folder now ships only what the plugin uses — skills, references, the three `#!` Python scripts, the README, LICENSE and the PNG icon — as the Claude plugin directory requires. The test apps moved to `evals/`, the unit tests to `tests/` and the icon's SVG source to `branding/`, all at the repository root (run the evals with `--eval-dir evals`).
- The icon PNG no longer carries EXIF metadata.
- The plugin folder's README no longer includes `/plugin install … --marketplace …` commands (the directory flags fetch-and-install lines as an install-time risk); install instructions stay in the repository README.

## 0.7.1 — 2026-11-18
### Changed
- Plugin, marketplace and repository descriptions now cover everything the plugin does (Kotlin and WebFlux, OpenAPI drift, the standalone checker, the `/validate-api` command and the GitHub Action).
- README overview updated; this changelog added.
- Ready for the Claude plugin directory: the plugin folder has its own README (install line, usage, and what the plugin runs, reads and sends) and LICENSE, and the icon is 512 px / 227 KiB (under the 256 KiB review limit).

## 0.7.0 — 2026-11-18
### Added
- **OpenAPI/Swagger contract comparison.** `scripts/openapi_spec.py` finds and reads OpenAPI 3 and Swagger 2 specs (YAML or JSON) with the Python standard library only.
- Quick-check rules **QC25–QC29**: documented operations with no handler (and undocumented handlers), documented vs. returned success status, documented-required fields the DTO doesn't enforce, spec/DTO property name and type drift, and springdoc `@ApiResponse`/`@Schema(required)` contradicting the code.
- `references/openapi.md` and a checklist section; test app `openapi-drift-orders`.

## 0.6.0 — 2026-11-18
### Changed
- **Cheaper reviews.** A one-line-per-rule `references/checklist.md` replaces reading every reference file up front; Kotlin and WebFlux rules moved to `kotlin.md` and `webflux.md` (read only for those stacks); `SKILL.md` cut by about 40%; explicit report-length rules. Measured on all test apps: 15% fewer tokens and 28% less time than 0.5.0, with accuracy unchanged.

## 0.5.0 — 2026-11-18
### Added
- **Kotlin and WebFlux coverage**: test apps `kotlin-books-api` and `webflux-shop-api`.
- `list_endpoints.py` lists functional routes (`RouterFunctions` builder, `route(GET(…))`, Kotlin `coRouter`).
- Quick-check rules **QC21–QC24**: functional handlers that never validate their body, `block()` in a WebFlux app, empty `Mono`/Kotlin `null` returned as 200 instead of 404, exceptions thrown from functional routes the `@ControllerAdvice` doesn't cover (WebFlux on Spring 5, or scoped advice).
- Kotlin-aware checks: non-null `Int` parameters as primitives, `findByIdOrNull()!!` as an unmapped 500.
### Fixed
- Global `@ControllerAdvice` *does* cover WebFlux functional routes since Spring 6.0 (verified against the Spring source); the references and rules now say so.
- A missing non-null Kotlin `Int` becomes 0, not a 400.

## 0.4.0 — 2026-11-18
### Added
- Quick-check rule **QC20 schema-limits**: request fields that allow longer strings or larger numbers than the database column they end up in, read from Flyway/SQL migrations, Liquibase XML and `@Column`.

## 0.3.2 — 2026-11-18
### Fixed
- Findings folded into another finding's PR comment are still counted at their own severity in the summary.
- "ProblemDetail" is only claimed when something actually enables it.

## 0.3.1 — 2026-11-18
### Fixed
- Lessons from the first real pull-request review: the most-misremembered Spring facts live in `SKILL.md` itself; a diff review is a smaller scope, not a lighter check; new write endpoints are compared with their siblings' authorization checks; inline comments are verified before posting and never "corrected" with a second comment.

## 0.3.0 — 2026-11-18
### Added
- `/spring-api-validator:validate-api` command: the whole API, a controller, `--diff [base]`, `--errors-only`, `--out`, and `--comment owner/repo/pull/N` to post findings on a pull request.
- The repository is a GitHub Action (`action.yml`): the quick check on a PR's changed files, as annotations and a job summary.
- Example workflows: a free quick check and a full Claude review on pull requests.
- `quick_check.py --diff-base`, `--format github|markdown`; CI for this repository.

## 0.2.0 — 2026-11-18
### Added
- `scripts/quick_check.py`: fast, deterministic checks for mechanical defects (QC01–QC19), JSON output and `--fail-on` for CI; regression tests.

## 0.1.2 — 2026-11-18
### Added
- Test apps from a real-app review (Boot 4 error dispatch, managed-club ownership, double-accepted transfers) and precision checks in every test case.
### Changed
- Severity calibration: rate by what happens today; suggested fixes must survive `@Transactional` rollback.

## 0.1.1 — 2026-11-17
### Added
- Plugin icon.

## 0.1.0 — 2026-11-17
### Added
- First release: the spring-api-validator skill (HTTP method semantics, binding, validation, DTOs, errors, structure; version-aware; project rules via `.api-validator.md`), `list_endpoints.py`, and the `spring-tools` marketplace.
