# Project API rules template

Teams can put a file named `.api-validator.md` at the repository root to describe their own API conventions. The validator reads it before checking endpoints, and these rules take precedence over the skill's generic defaults. Offer this template when a project has none and the report would benefit from team decisions (e.g. it flagged a pattern that may be intentional).

Only the sections a team cares about need to be filled in; anything left out falls back to the defaults.

```markdown
# API rules

## Paths
- Prefix: /api/v1 (set via class-level @RequestMapping)
- Segments: plural nouns, kebab-case
- Path variable names: {orderId} style (resource name + Id)
- Actions on resources: POST /{resource}/{id}/{action} is allowed (e.g. /orders/{orderId}/cancel)

## HTTP methods and statuses
- Create: POST, returns 201 with Location header and the created resource
- Update: PATCH for partial updates; PUT is not used
- Delete: soft delete, returns 204; deleting a missing resource returns 404
- Search with complex filters: POST /{resource}/search is allowed

## Request/response objects
- DTOs are Java records in the `api` package of each feature: XxxRequest / XxxResponse
- JSON naming: snake_case (set globally via spring.jackson.property-naming-strategy)
- Money: BigDecimal serialized as string
- Timestamps: OffsetDateTime, ISO-8601
- Never return @Entity classes

## Errors
- All errors use ProblemDetail via GlobalExceptionHandler; never build error bodies in controllers
- Validation errors: 400 with an `errors` array of {field, message}

## Pagination
- Collections are paginated with page/size; max size 100; response is PagedModel

## Security
- Every write endpoint has @PreAuthorize

## Exceptions / accepted deviations
- LegacyReportController is frozen; report issues as suggestions only
```
