from prometheus_client import Counter

# ── Auth metrics ──────────────────────────────────────────────

AUTH_REQUESTS_TOTAL = Counter(
    "auth_requests_total",
    "Total authorization requests",
    ["endpoint", "method"],
)

AUTH_ERRORS_TOTAL = Counter(
    "auth_errors_total",
    "Total authorization errors",
    ["endpoint", "error_type"],
)

AUTH_SUCCESS_LOGINS_TOTAL = Counter(
    "auth_success_logins_total",
    "Total successful logins",
)

# ── User creation metrics ─────────────────────────────────────

USER_CREATION_ERRORS_TOTAL = Counter(
    "user_creation_errors_total",
    "Total errors creating users",
    ["error_type"],
)
