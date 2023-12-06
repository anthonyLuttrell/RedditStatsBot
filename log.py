import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="json/debug.log",
)

handler = logging.StreamHandler(sys.stderr)
handler.addFilter(lambda record: record.levelno >= logging.WARNING)


def debug(*args: str) -> None:
    debug_message = ""
    for arg in args:
        debug_message += arg
    logging.debug(debug_message)


def info(*args: str) -> None:
    info_message = ""
    for arg in args:
        info_message += arg
    logging.info(info_message)


def warn(*args: str) -> None:
    warning_message = ""
    for arg in args:
        warning_message += arg
    logging.warning(warning_message)


def error(*args: str) -> None:
    error_message = ""
    for arg in args:
        error_message += arg
    logging.error(error_message)


def critical(*args: str) -> None:
    critical_message = ""
    for arg in args:
        critical_message += arg
    logging.critical(critical_message)
