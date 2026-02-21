"""Ada Core API — Entry Point."""

import logging
import os

import uvicorn

from server.config import get_settings


def main():
    """Run the Ada Core API server."""
    cfg = get_settings()
    is_dev = os.getenv("ADA_ENV", "production") == "development"

    logging.basicConfig(
        level=getattr(logging, cfg.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",
        port=cfg.port,
        reload=is_dev,
        log_level=cfg.log_level,
    )


if __name__ == "__main__":
    main()
