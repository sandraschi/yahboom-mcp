import logging

logger = logging.getLogger("yahboom-mcp")


def fail_response(message: str, *, error: str | None = None, **extra) -> dict:
    return {"success": False, "message": message, "error": error or message, **extra}


def _error_response(message: str, *, error: str | None = None, **extra) -> dict:
    """Shared error helper (TOOL_DESIGN_STANDARDS §7.1 Pattern 3).

    Call from inside an ``except`` block: captures the traceback via
    ``logger.exception`` and returns the dialogic failure shape.
    """
    logger.exception("yahboom-mcp error: %s", message)
    return fail_response(message, error=error, **extra)


from .server import main


def hello() -> str:
    return "Hello from yahboom-mcp!"


__all__ = ["_error_response", "fail_response", "hello", "main"]
