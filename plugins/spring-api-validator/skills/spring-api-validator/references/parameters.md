# Parameters, binding and mapping

How Spring MVC binds path, query, header and body values to Java parameters, and where that breaks. Each item says what happens at runtime, because that decides severity.

## Parameter names and `-parameters`

`@PathVariable Long id`, `@RequestParam String status` without an explicit name rely on the compiled parameter name.

- **Spring Framework 6.1+ (Boot 3.2+)** only reads names from the `-parameters` compiler flag (the debug-info fallback was removed). Without it, every request to that handler fails with `IllegalArgumentException: Name for argument of type [...] not specified, and parameter name information not available via reflection` → **500**.
- `spring-boot-starter-parent` (Maven) and the `org.springframework.boot` Gradle plugin enable `-parameters` automatically. So only flag this when the project uses neither — e.g. a Maven BOM import (`spring-boot-dependencies` in `dependencyManagement`) with a custom `maven-compiler-plugin` config lacking `<parameters>true</parameters>`, or a Gradle build without the Boot plugin. Kotlin needs `-java-parameters` (the `kotlin-spring` setup from start.spring.io adds it).
- Boot 2 / Spring 5 fall back to debug info, which Maven and Gradle compile in by default, so this is not an issue there.
- Explicit names (`@PathVariable("id")`) are always safe.

## `@PathVariable`

- **Name must match the URI template variable**: `@DeleteMapping("/{orderId}")` with `@PathVariable Long id` → `MissingPathVariableException` → **500** (Spring treats it as a programming error, not a client error). Check every handler: template variables vs parameter names (or explicit names).
- Every template variable should be bound, and every `@PathVariable` should exist in the template (class-level + method-level combined).
- Type conversion failure (`/orders/abc` for `Long id`) → `MethodArgumentTypeMismatchException` → 400. Fine, but check the error body is consistent with the API's error format (see `responses-errors.md`).
- `required = false` on a path variable only makes sense when another mapping on the same handler omits it; otherwise it's misleading.
- Values containing `/` need `{*path}` or a regex; values with dots are captured fully in Spring 5.3+/6 (suffix pattern matching is off).

## `@RequestParam`

- Default `required = true`: a missing parameter → `MissingServletRequestParameterException` → 400. Check that optional filters are actually marked optional (`required = false`, `defaultValue`, or `Optional<T>`).
- **`required = false` on a primitive** (`int page`, `boolean active`) with the parameter absent → `IllegalStateException: Optional int parameter 'page' is present but cannot be translated into a null value` → **500**. Fix: `defaultValue = "0"`, or a wrapper type (`Integer`), or `Optional<Integer>`.
- `defaultValue` implies `required = false`; combining `required = true` with `defaultValue` is contradictory (the default wins).
- **Dates/times**: `LocalDate`, `LocalDateTime`, `Instant` query params without `@DateTimeFormat(iso = ...)` (and without `spring.mvc.format.date/date-time` set globally) are parsed with a locale-dependent short style first. Before Spring Framework 6.1, ISO input like `2026-11-17` then fails → 400 (Warning). From 6.1 (Boot 3.2+) the parser falls back to ISO, so ISO input binds and the locale-style formats are accepted too — a Suggestion to make the accepted format explicit, not a bug.
- **Enums**: converted with `Enum.valueOf` — case-sensitive, so `?status=open` fails for `OPEN` → 400. Fine if documented; flag if the API elsewhere uses lowercase values or the docs show lowercase.
- **Collections**: `List<Long> ids` binds `?ids=1,2,3` and `?ids=1&ids=2`. Unbounded lists can be a performance concern — mention for public APIs.
- **Paging/sorting**: `Pageable` parameters accept any `sort` property name; sorting by unindexed or sensitive properties may be possible. `size` is capped by `spring.data.web.pageable.max-page-size` (default 2000). Suggest a whitelist / smaller cap for public APIs.
- Many individual `@RequestParam`s for one filter (5+) suggest a filter object bound with `@ModelAttribute` (or a record), which also allows validation of the group.

## `@RequestHeader`, `@CookieValue`

Same `required` and primitive rules as `@RequestParam`. Missing required header → `MissingRequestHeaderException` → 400. Header names are case-insensitive.

## `@RequestBody`

- **At most one** `@RequestBody` per handler — the body stream can be read once. A second one fails at request time.
- Default `required = true`: empty body → `HttpMessageNotReadableException` → 400.
- On GET/DELETE: see `http-methods.md`.
- Malformed JSON, wrong JSON types (`"quantity": "abc"`), unknown enum values → `HttpMessageNotReadableException` → 400 by default. Make sure a custom `@ExceptionHandler(Exception.class)` doesn't turn these into 500s.
- `consumes` restriction: without it, any supported content type is accepted; with it, others → 415. Only flag mismatch with documentation or the rest of the API.

## Mapping definitions

- **`@RequestMapping` without `method`** on a handler method matches *all* HTTP methods (GET, POST, PUT, DELETE, PATCH…). Error severity when the handler writes data; warning otherwise. (On the class level it's normal — it only sets the base path.)
- **Duplicate mappings** (same verb + same pattern on two handlers) fail at startup with `IllegalStateException: Ambiguous mapping`.
- **Equally specific patterns** — `/users/{id}` and `/users/{name}` with the same verb — register fine but every matching request fails with `Ambiguous handler methods mapped` → 500. Literal segments win over variables, so `/users/me` vs `/users/{id}` is fine.
- **`params`/`headers`/`produces`** conditions that differ between two otherwise identical mappings are legitimate (content negotiation, versioning by header); check they don't overlap.
- Paths built from constants (`@GetMapping(ApiPaths.ORDER_BY_ID)`) — resolve the constant before judging.
- `server.servlet.context-path`, `spring.mvc.servlet.path` and `WebMvcConfigurer.configurePathMatch(addPathPrefix(...))` change the real URL; include them in the inventory.

## WebFlux notes

The same annotations apply. Differences that matter: no servlet context path (use `spring.webflux.base-path`), validation errors surface as `WebExchangeBindException`, and returning `Mono.empty()` from a handler yields 200 with an empty body — not 404 (see `responses-errors.md`).

- **Functional routes** (`RouterFunctions.route().GET("/x", handler::m)`, `route(GET("/x"), …)`, Kotlin `coRouter { }`) are endpoints too: include them in the inventory with their handler, and resolve nested prefixes (`.path("/api", …)`, `.nest`, `"/api".nest { }`) by reading the router. Path variables come from `request.pathVariable("x")` — a name that isn't in the route template throws `IllegalArgumentException` (500).
- **Blocking on the event loop**: `.block()`, `.blockFirst()`, `.blockLast()`, `.toFuture().get()` in code that runs on a request in a WebFlux app throw `IllegalStateException` ("block()/blockFirst()/blockLast() are blocking, which is not supported in thread reactor-http-nio-…") — every such request fails with 500. `block()` subscribes first and checks the thread afterwards, so the upstream call (an HTTP request, a query) is still started and its side effects can happen before the exception. Blocking JDBC/JPA repositories called from a reactive handler don't throw, but stall the event loop. Flag both; the fix is to stay reactive (`flatMap`) or move blocking work to `Schedulers.boundedElastic()`.
