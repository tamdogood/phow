"""Domain errors for Reputation Hub services."""


class ReviewServiceError(Exception):
    """Base service error that maps to API error taxonomy."""

    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class ValidationFailedError(ReviewServiceError):
    def __init__(self, message: str):
        super().__init__("validation_failed", message, 400)


class OwnershipForbiddenError(ReviewServiceError):
    def __init__(self, message: str = "You do not own this resource"):
        super().__init__("ownership_forbidden", message, 403)


class AuthExpiredError(ReviewServiceError):
    def __init__(self, message: str = "Authentication expired. Reconnect source"):
        super().__init__("auth_expired", message, 401)


class IdempotencyConflictError(ReviewServiceError):
    def __init__(self, message: str = "Duplicate publish request"):
        super().__init__("idempotency_conflict", message, 409)


class ProviderUnavailableError(ReviewServiceError):
    def __init__(self, message: str = "Provider unavailable"):
        super().__init__("provider_unavailable", message, 503)


class PolicyBlockedError(ReviewServiceError):
    def __init__(self, message: str = "Response blocked by policy"):
        super().__init__("policy_blocked", message, 422)


class RateLimitedError(ReviewServiceError):
    def __init__(self, message: str = "Provider rate limited"):
        super().__init__("rate_limited", message, 429)
