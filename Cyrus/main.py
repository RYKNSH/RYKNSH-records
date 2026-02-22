"""Cyrus entrypoint."""

import uvicorn

from models.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "server.app:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
