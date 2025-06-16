import logging
import sys
from logging.handlers import TimedRotatingFileHandler

LOG_FILE = "backend/logs/app.log"

def setup_logging():
    """
    Configures the logging for the application.
    """
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)

    # Prevent logs from being propagated to the root logger
    logger.propagate = False

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console Handler
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    # File Handler (rotating)
    if not any(isinstance(h, TimedRotatingFileHandler) for h in logger.handlers):
        file_handler = TimedRotatingFileHandler(
            LOG_FILE, when="midnight", interval=1, backupCount=7, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

# Create logs directory if it doesn't exist
import os
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logger = setup_logging() 