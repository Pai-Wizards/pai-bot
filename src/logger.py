import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)


bot_logger = logging.getLogger("bot_logger")


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def set_log_level(level: int) -> None:
    logging.getLogger().setLevel(level)
    bot_logger.setLevel(level)


def log_info(message: str) -> None:
    bot_logger.info(message)


def log_debug(message: str) -> None:
    bot_logger.debug(message)


def log_warning(message: str) -> None:
    bot_logger.warning(message)


def log_error(message: str) -> None:
    bot_logger.error(message)


def log_critical(message: str) -> None:
    bot_logger.critical(message)