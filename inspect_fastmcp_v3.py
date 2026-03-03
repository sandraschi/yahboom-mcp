from fastmcp import FastMCP
import inspect

mcp = FastMCP("test")
print(f"http_app type: {type(mcp.http_app)}")
print(f"custom_route signature: {inspect.signature(mcp.custom_route)}")
