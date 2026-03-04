from fastmcp import FastMCP
from fastapi import FastAPI
import uvicorn

app = FastAPI()


@app.get("/health")
async def health():
    return {"status": "ok"}


mcp = FastMCP.from_fastapi(app)

import starlette.applications

print(f"Is mcp a Starlette app? {isinstance(mcp, starlette.applications.Starlette)}")
print(f"mcp type: {type(mcp)}")
print(f"mcp dir: {[a for a in dir(mcp) if not a.startswith('_')]}")

# Check for routes if it's a starlette app
if hasattr(mcp, "routes"):
    print("Routes in mcp:")
    for route in mcp.routes:
        print(f"  {route.path} -> {route.name}")
else:
    print("mcp has no 'routes' attribute")

# If from_fastapi(app) was used, maybe 'app' is stored somewhere else
# Search for 'app' in internal attributes
print(
    f"Internal attributes containing 'app': {[a for a in dir(mcp) if 'app' in a.lower()]}"
)

print(f"Custom routes in 'app': {[r.path for r in app.routes]}")

# Let's see if mcp has an 'app' attribute or something similar
try:
    print(f"mcp.app type: {type(mcp.app)}")
    print("Routes in mcp.app:")
    for route in mcp.app.routes:
        print(f"  {route.path} -> {route.name}")
except Exception as e:
    print(f"Could not access mcp.app or routes: {e}")

# Try to see if there's an internal starlette app
try:
    from starlette.applications import Starlette

    if isinstance(mcp, Starlette):
        print("FastMCP instance is itself a Starlette app")
except:
    pass
