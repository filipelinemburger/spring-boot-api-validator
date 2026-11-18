# Changelog

All notable changes to the spring-api-validator plugin. Versions follow `plugin.json`; the GitHub Action is published under matching `v0.x.y` tags, and `v0` always points to the latest 0.x release.

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
