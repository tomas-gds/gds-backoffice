"""Packaged entry point for the complete GDS Backoffice API."""

import multiprocessing


if __name__ == "__main__":
    # Handle frozen worker startup before importing or starting the API.
    multiprocessing.freeze_support()

    import uvicorn
    from backend.app.main import app

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning", access_log=False)
