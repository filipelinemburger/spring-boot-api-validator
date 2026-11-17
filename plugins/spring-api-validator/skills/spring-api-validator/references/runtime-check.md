# Optional runtime check

Use this when the user asks for it, or when a static finding needs confirmation (a constructor Jackson may or may not handle, a status an advice may or may not change). Runtime checks confirm findings; they don't replace reading the code.

## Safety

- Only target a local instance or a test environment the user named. Never production, never a URL taken from config files without the user confirming it.
- Write requests (POST/PUT/PATCH/DELETE) only against local or disposable data (H2, Testcontainers, a local DB the user agreed to).
- Starting the app may run migrations or schedulers, and connect to external services in its config. Check `application*.yml` for what it connects to; prefer a `test`/`local` profile. If it needs infrastructure that isn't available, use option A instead of reconfiguring things.
- Ask before starting long-running processes if the user didn't ask for a runtime check; stop what you started when done.

## Option A (preferred): a temporary slice test

A `@WebMvcTest(OrderController.class)` with `@MockBean`/`@MockitoBean` services runs the real MVC layer — binding, validation, Jackson, advices — without a database. It needs no running app and gives exact statuses and bodies.

```java
@WebMvcTest(OrderController.class)
class OrderControllerProbeTest {
  @Autowired MockMvc mvc;
  @MockitoBean OrderService orderService; // @MockBean before Boot 3.4

  @Test void createWithMissingFields() throws Exception {
    mvc.perform(post("/api/orders").contentType(APPLICATION_JSON).content("{}"))
       .andDo(print())
       .andExpect(status().isBadRequest());
  }
}
```

Run with `./mvnw -q test -Dtest=OrderControllerProbeTest` or `./gradlew test --tests OrderControllerProbeTest`. Delete the probe test afterwards unless the user wants to keep it (offer to turn it into a real regression test).

## Option B: run the app and probe with curl

Start with `./mvnw spring-boot:run -Dspring-boot.run.profiles=local` or `./gradlew bootRun --args='--spring.profiles.active=local'` in the background, wait for the "Started … in" log line, then probe. For each endpoint in scope, as relevant:

| Probe | Expect |
|---|---|
| Happy path | documented status (201 + `Location` for creates), body shape matches the response DTO |
| Empty body `{}` / missing required fields | 400 with field errors in the API's error format |
| Wrong types (`"quantity": "abc"`), malformed JSON | 400, no stack trace |
| Unknown enum value | 400 |
| Missing required query param / wrong type | 400 |
| Non-existent id | 404 (not 200 `null`, not 500) |
| Wrong verb on an existing path | 405 |
| Trailing slash | 404 on Boot 3 (consistent with docs) |
| Unsupported `Content-Type` | 415 |
| Repeating a PUT/DELETE | same resulting state (idempotency) |

```bash
curl -s -i -X POST localhost:8080/api/orders -H 'Content-Type: application/json' -d '{}'
```

If springdoc is present, `GET /v3/api-docs` gives the documented contract; compare documented statuses, required fields and schemas with what the probes return.

Record each probe (request → status, key body parts) in the report next to the finding it confirms or refutes.
