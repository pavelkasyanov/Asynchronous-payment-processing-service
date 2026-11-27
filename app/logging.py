import logging
import sys

from app.config import get_settings


def setup_logging() -> None:
    settings = get_settings()

    logging.basicConfig(
        level=settings.LOG_LEVEL.upper(),
        format=settings.LOG_FORMAT,
        datefmt=settings.LOG_DATE_FORMAT,
        stream=sys.stdout,
        force=True,
    )

    logging.getLogger(__name__).info(
        "Logging initialized: %s",
        settings.LOG_LEVEL,
    )