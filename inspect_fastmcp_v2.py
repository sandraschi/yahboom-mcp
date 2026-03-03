from fastmcp import FastMCP
import json

mcp = FastMCP("test")
attrs = [a for a in dir(mcp) if not a.startswith("__")]
print(json.dumps(attrs, indent=2))
