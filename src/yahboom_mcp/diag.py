import sys
import os
from contextlib import asynccontextmanager

# Add parent to path to mimic server.py environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from fastmcp import FastMCP

    print(f"FastMCP Source: {FastMCP.__module__}")

    @asynccontextmanager
    async def dummy_lifespan(app):
        yield

    mcp = FastMCP("Test", lifespan=dummy_lifespan)
    print(f"mcp type: {type(mcp)}")
    print(f"mcp attributes: {dir(mcp)}")
    print(f"mcp.app exists: {hasattr(mcp, 'app')}")
    if hasattr(mcp, "app"):
        print(f"mcp.app type: {type(mcp.app)}")
    else:
        print("CRITICAL: mcp.app IS MISSING")
except Exception as e:
    print(f"DIAG ERROR: {e}")
