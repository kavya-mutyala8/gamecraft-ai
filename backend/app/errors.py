"""Typed application errors.

Every error that reaches a client is rendered as:

    {"error": {"code": "...", "message": "...", "details": ..., "request_id": "..."}}

Internal exception text is logged, never returned.
"""

from typing import Any


class AppError(Exception):
    status_code = 500
    code = "INTERNAL_ERROR"
    default_message = "An unexpected error occurred."

    def __init__(
        self,
        message: str | None = None,
        *,
        details: Any = None,
        retry_after: float | None = None,
    ):
        self.message = message or self.default_message
        self.details = details
        self.retry_after = retry_after
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"
    default_message = "The requested resource was not found."


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"
    default_message = "The request conflicts with the current state of the resource."


class ContentBlockedError(AppError):
    """The AI provider's safety system refused the prompt or the output."""

    status_code = 422
    code = "CONTENT_BLOCKED"
    default_message = "The AI provider blocked this request. Try rephrasing the concept or prompt."


class RateLimitedError(AppError):
    status_code = 429
    code = "RATE_LIMITED"
    default_message = "Too many requests. Please slow down and retry shortly."


class UpstreamError(AppError):
    status_code = 502
    code = "UPSTREAM_ERROR"
    default_message = "The AI provider failed to process the request."


class UpstreamRejectedError(AppError):
    """Provider rejected the request itself (bad params); retrying will not help."""

    status_code = 502
    code = "AI_REQUEST_REJECTED"
    default_message = "The AI provider rejected the request."


class UpstreamTimeoutError(AppError):
    status_code = 504
    code = "UPSTREAM_TIMEOUT"
    default_message = "The AI provider took too long to respond."


class AIResponseError(AppError):
    """Provider answered, but the answer was unusable (bad JSON, no image...)."""

    status_code = 502
    code = "AI_BAD_RESPONSE"
    default_message = "The AI provider returned an unusable response."


class ServiceUnavailableError(AppError):
    status_code = 503
    code = "SERVICE_UNAVAILABLE"
    default_message = "The service is temporarily unavailable."


# Errors worth retrying with backoff.
RETRYABLE = (UpstreamError, UpstreamTimeoutError, RateLimitedError, AIResponseError)
