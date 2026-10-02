"""Packaged entry point for the local Database Mapper API."""

import uvicorn

from backend.app.main import app


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="warning",
        access_log=False,
    )
