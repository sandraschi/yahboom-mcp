from fastmcp import FastMCP

mcp = FastMCP("test")
app = mcp.http_app()
print(f"app type: {type(app)}")
try:
    from fastapi import FastAPI

    print(f"Is FastAPI: {isinstance(app, FastAPI)}")
except ImportError:
    print("FastAPI not available for check")
