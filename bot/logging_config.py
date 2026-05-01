from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys


LOGGER_NAME = "trading_bot"
LOG_DIRECTORY = Path("logs")
LOG_FILE_PATH = LOG_DIRECTORY / "trading_bot.log"
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(filename)s]  — %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger(LOGGER_NAME)
    root_logger.setLevel(logging.DEBUG)

    if not root_logger.handlers:
        formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

        file_handler = RotatingFileHandler(
            filename=LOG_FILE_PATH,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        root_logger.propagate = False

    return root_logger.getChild(name)

