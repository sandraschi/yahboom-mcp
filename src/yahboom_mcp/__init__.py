def fail_response(message: str, *, error: str | None = None, **extra) -> dict:
    return {"success": False, "message": message, "error": error or message, **extra}


from .server import main


def hello() -> str:
    return "Hello from yahboom-mcp!"


__all__ = ["fail_response", "hello", "main"]
