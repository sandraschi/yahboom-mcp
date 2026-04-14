from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastmcp import FastMCP


@asynccontextmanager
async def ls(m):
    print("Lifespan start")
    yield
    print("Lifespan end")


app = FastAPI()
try:
    mcp = FastMCP.from_fastapi(app, name="test", lifespan=ls)
    print("FastMCP.from_fastapi success with lifespan")
    # Verify we can run it (briefly)
    # asyncio.run(mcp.run_stdio_async())
except Exception as e:
    print(f"Error: {e}")
