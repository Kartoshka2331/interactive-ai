import sys
import logging
from loguru import logger
from api.config.settings import settings


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        frame = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def format_record(record: dict) -> str:
    if record["message"].endswith("."):
        record["message"] = record["message"][:-1]

    format_string = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>\n"
    )
    return format_string


def setup_logging():
    logging.root.handlers = [InterceptHandler()]

    logging.root.setLevel(settings.log_level)

    logger.remove()

    logger.add(
        sys.stderr,
        level=settings.log_level,
        format=format_record
    )

    logger.add(
        settings.log_file,
        rotation="10 MB",
        retention="1 month",
        compression="zip",
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )

    libraries_to_silence = [
        "asyncssh",
        "httpx",
        "httpcore",
        "urllib3",
        "watchfiles",
        "multipart"
    ]

    for library_name in libraries_to_silence:
        logging_logger = logging.getLogger(library_name)
        logging_logger.setLevel(logging.WARNING)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.propagate = False
