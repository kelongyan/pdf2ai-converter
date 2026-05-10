from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import files, convert, config, ws


def create_app() -> FastAPI:
    app = FastAPI(title="PDF2AI Converter", version="3.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(files.router, prefix="/api")
    app.include_router(convert.router, prefix="/api")
    app.include_router(config.router, prefix="/api")
    app.include_router(ws.router, prefix="/api")

    dist_dir = Path(__file__).resolve().parent.parent / "web" / "dist"
    if dist_dir.exists():
        app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="static")

    return app
