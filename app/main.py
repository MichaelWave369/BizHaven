import threading

import uvicorn

from app.api.server import app as fastapi_app


def run_api() -> None:
    uvicorn.run(fastapi_app, host="127.0.0.1", port=8090, log_level="warning")


def start_embedded_api() -> threading.Thread:
    thread = threading.Thread(target=run_api, daemon=True)
    thread.start()
    return thread
