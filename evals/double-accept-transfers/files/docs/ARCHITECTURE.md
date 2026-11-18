# transfer-market

Internal service behind the platform API gateway. The gateway authenticates every request and only forwards
calls whose `buyerClubId` / `borrowerClubId` belong to the caller's club, so this service does not
authenticate or authorise requests itself.

Money columns are `NUMERIC`; amounts are `BigDecimal` end to end.
