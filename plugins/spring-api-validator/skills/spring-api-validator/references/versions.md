# Version-dependent behaviour

Read the Spring Boot version from the build file (parent version, `org.springframework.boot` plugin version, or the `spring-boot-dependencies` BOM) and use this table before reporting a version-dependent finding. Spring Framework version follows Boot: Boot 2.7 → Framework 5.3, Boot 3.0 → 6.0, 3.1 → 6.0, 3.2 → 6.1, 3.3 → 6.1, 3.4 → 6.2, 3.5 → 6.2.

| Topic | Boot 2.x (Spring 5.3) | Boot 3.0–3.1 (Spring 6.0) | Boot 3.2+ (Spring 6.1+) |
|---|---|---|---|
| Validation / Servlet / JPA namespace | `javax.*` | `jakarta.*` | `jakarta.*` |
| Java baseline | 8+ | 17+ | 17+ |
| Validation starter needed | yes (since 2.3) | yes | yes |
| Parameter names without `-parameters` | work (debug info fallback) | work, with a deprecation warning | **fail → 500** (Boot parent / Gradle plugin set the flag) |
| Trailing slash `/orders/` matches `/orders` | yes | **no** | no |
| Constraints on `@PathVariable`/`@RequestParam` | need class-level `@Validated`; `ConstraintViolationException` (500 unless handled) | same as 2.x | **built-in** method validation → `HandlerMethodValidationException` (400); class-level `@Validated` switches back to the AOP path |
| `ProblemDetail` (RFC 7807/9457) | not available | available; `spring.mvc.problemdetails.enabled` | available |
| Missing static resource / unknown path | `NoHandlerFoundException` only if configured | same | `NoResourceFoundException` → 404 (make sure catch-all advice doesn't turn it into 500) |
| Path matching default | `PathPatternParser` since 2.6 | `PathPatternParser` | `PathPatternParser` |
| Spring Data `deleteById(missing)` | throws `EmptyResultDataAccessException` (Data 2.x) | silently ignores (Data 3.x) | silently ignores |
| `Page<T>` JSON serialization | serialized as-is (verbose) | as-is | 3.3+: warning, use `PagedModel` / `VIA_DTO` |
| `spring.jpa.open-in-view` default | true (warns) | true (warns) | true (warns) |

**Boot 4.x (Spring Framework 7, Security 7, Data 4, Hibernate 7, Java 17+)** builds on the 3.2+ column: method validation, `-parameters`, no trailing-slash match, Data's silent `deleteById` all carry over. Differences to account for (confirm against the project's dependency tree when a finding depends on one):
- **Jackson 3** is the default: databind lives in `tools.jackson.*` (e.g. `tools.jackson.databind.ObjectMapper`), while the annotations stay in `com.fasterxml.jackson.annotation`. Customisation goes through the Jackson 3 builder customizers rather than `Jackson2ObjectMapperBuilderCustomizer`; look for both. Jackson 3 changed several defaults compared with 2.x — don't assume the 2.x behaviour for things like null-for-primitive or date handling without checking the version and config.
- `HttpStatus.UNPROCESSABLE_ENTITY` is superseded by `UNPROCESSABLE_CONTENT` (same 422).
- Spring Security 7 still authorises every dispatcher type, so the error-dispatch problem in `responses-errors.md` applies.

Notes:
- **Boot 2.x is out of open-source support** (2.7 OSS support ended in 2023). Mention once in the summary as context, not as a finding per endpoint, and don't recommend Boot 3-only features (like `ProblemDetail`) as fixes for a Boot 2 project — offer the Boot 2 equivalent and, optionally, note the upgrade path.
- **WebFlux** projects: replace servlet-specific advice (context path, `HttpServletRequest`) with the reactive equivalents; validation and Jackson rules are the same.
- **Kotlin**: check `jackson-module-kotlin` is present (Boot adds it with the Kotlin starter setup); without it, data classes without default values can't be deserialized.
- If the version can't be determined (multi-module build with the version elsewhere), find the parent POM/version catalog; if still unknown, state the assumption in the report.
