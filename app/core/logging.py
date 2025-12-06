from __future__ import annotations

import logging
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("app")
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(level)

    if logger.handlers:
        return logger

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")

    stream = logging.StreamHandler()
    stream.setFormatter(fmt)
    logger.addHandler(stream)

    if os.getenv("LOG_TO_FILE", "1") == "1":
        try:
            file_handler = logging.FileHandler(LOG_DIR / "app.log")
            file_handler.setFormatter(fmt)
            logger.addHandler(file_handler)
        except OSError as exc:
            # Fall back silently if log file is not writable (e.g., mounted volume permissions)
            logger.warning("File logging disabled: %s", exc)

    return logger


logger = setup_logger()


