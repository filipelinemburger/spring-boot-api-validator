# WebFlux and functional endpoints

Read when the app uses Spring WebFlux, or functional routes (`RouterFunction`, Kotlin `coRouter`, WebMvc.fn). Everything in the checklist still applies; these are the differences.

## Paths and inventory
- No servlet context path: `spring.webflux.base-path` prefixes every route (annotated and functional).
- Functional routes are endpoints: `RouterFunctions.route().GET("/x", handler::m)`, `route(GET("/x"), …)`, `coRouter { GET("/x", …) }`. Resolve nested prefixes (`.path("/api", …)`, `.nest`, `"/api".nest { }`) by reading the router. `request.pathVariable("x")` with a name not in the template → `IllegalArgumentException` 500.

## Validation
- Annotated handlers: `@Valid @RequestBody` works; failures raise `WebExchangeBindException` (400 by default; check the advice maps it).
- **Functional handlers get no Bean Validation at all.** `request.bodyToMono(X.class)` / `request.body(X.class)` / `awaitBody<X>()` ignore every constraint on `X` unless the handler calls a `Validator` itself and turns violations into a 400 (**Error**). Spell out what the unchecked values do downstream (negative quantities, blank ids).

## Responses and errors
- A `Mono` that completes empty → 200 with no body, not 404 (Warning; Error on a common path). Use `switchIfEmpty(Mono.error(new ResponseStatusException(NOT_FOUND)))` or `defaultIfEmpty(ResponseEntity.notFound().build())`.
- `@ControllerAdvice` and functional routes, by version:
  - WebFlux on Spring Framework 6.0+ (Boot 3+): `DispatcherHandler` passes errors from every handler, functional ones included, to `RequestMappingHandlerAdapter.handleError`, so **global** advice handles them. Advice scoped with `basePackages`/`assignableTypes`/`annotations` doesn't (no controller type to match).
  - WebFlux on Spring 5.x (Boot 2.x): advice covers annotated controllers only; exceptions from functional handlers reach the default handling (usually 500).
  - WebMvc.fn: global advice applies since 5.3; scoped advice doesn't.
  - Where advice doesn't apply, the exception needs `@ResponseStatus`/`ResponseStatusException`, or handling in the route (`onErrorResume`, `.onError(…)`, a `HandlerFilterFunction`).

## Blocking
- `.block()`, `.blockFirst()`, `.blockLast()`, `.toFuture().get()` on a request (event-loop) thread → `IllegalStateException` ("block()/blockFirst()/blockLast() are blocking, which is not supported in thread reactor-http-nio-…") → 500 (**Error**). `block()` subscribes before it checks the thread, so the upstream call may already have started. Fix: stay reactive (`flatMap`).
- Blocking JDBC/JPA or file I/O called from a reactive handler doesn't throw but stalls the event loop (Warning); move it to `Schedulers.boundedElastic()` or use reactive drivers.
- `WebClient` calls without a timeout hang a request as long as the remote does (Suggestion/Warning).
