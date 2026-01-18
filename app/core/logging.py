"""Logging configuration for Namaskah application."""

import logging
import os
import sys
from pathlib import Path


def setup_logging():
    """Setup logging configuration."""
    handlers = [logging.StreamHandler(sys.stdout)]

    # Only create file handler in development (not on Render/production)
    if os.environ.get("RENDER") is None:
        try:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            handlers.append(logging.FileHandler(log_dir / "app.log"))
        except (PermissionError, OSError):
            # Can't create logs directory, use stdout only
            pass

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
