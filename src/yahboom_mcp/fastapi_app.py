from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os


def create_app():
    app = FastAPI(title="Yahboom ROS 2 SOTA Dashboard")

    # Static files for the React frontend
    # app.mount("/static", StaticFiles(directory="frontend/dist"), name="static")

    @app.get("/api/v1/health")
    async def health():
        return {"status": "ok", "service": "yahboom-mcp"}

    return app
