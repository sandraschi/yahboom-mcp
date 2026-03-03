from fastmcp import FastMCP
from fastapi.responses import JSONResponse

mcp = FastMCP("test")
app = mcp.http_app()


@app.get("/test")
async def test_route():
    return JSONResponse({"status": "ok"})


print("Successfully defined route on app")
