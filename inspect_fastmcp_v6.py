from fastmcp import FastMCP
from starlette.responses import JSONResponse

mcp = FastMCP("test")


@mcp.custom_route("/test", methods=["GET"])
async def test_route(request):
    return JSONResponse({"status": "ok"})


print("Successfully defined custom route")
