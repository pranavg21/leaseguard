"""Exception types and the single helper used to describe errors safely."""


class LeaseGuardError(Exception):
    """Base class for errors whose message is safe to show to users."""

    code = "leaseguard_error"


class IngestError(LeaseGuardError):
    """Raised when an uploaded or pasted document is rejected."""

    code = "invalid_document"


def describe_error(error: BaseException) -> str:
    """Return a log-safe one-line description of an exception.

    Args:
        error: Any exception.

    Returns:
        The exception class name and its message, without a traceback.
    """
    message = str(error).splitlines()[0] if str(error) else ""
    return f"{type(error).__name__}: {message}" if message else type(error).__name__
