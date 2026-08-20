import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

# Define custom SUCCESS log level
SUCCESS_LEVEL_NUM = 25
logging.addLevelName(SUCCESS_LEVEL_NUM, "SUCCESS")


def success(self, message, *args, **kws):
    if self.isEnabledFor(SUCCESS_LEVEL_NUM):
        self._log(SUCCESS_LEVEL_NUM, message, args, **kws)


logging.Logger.success = success


def get_app_root():
    """
    Returns the writable application directory.

    Python:
        Project root

    PyInstaller EXE:
        Directory containing the EXE
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parents[2]


def setup_logger():
    app_root = get_app_root()

    log_dir = app_root / "Output" / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("enterprise_harvester")
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    log_file = log_dir / "app.log"

    file_handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )

    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info(f"Log directory: {log_dir}")

    return logger


logger = setup_logger()