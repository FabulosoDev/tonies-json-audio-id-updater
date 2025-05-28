import logging
import os
import sys
from typing import Optional

class LoggerFactory:
    def __init__(self):
        # Get log level from environment variable, default to INFO if not set
        log_level_name = os.getenv('LOG_LEVEL', 'INFO').upper()
        try:
            self.level = getattr(logging, log_level_name)
        except AttributeError:
            print(f"Invalid log level: {log_level_name}, using INFO")
            self.level = logging.INFO

        self.handler = logging.StreamHandler(sys.stdout)
        self.handler.setFormatter(_ColourFormatter())

        logger = logging.getLogger(__name__)
        logger.debug(f"Logger initialized with level: {log_level_name}")

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a configured logger instance with colored output

        Args:
            name: The name of the logger (typically __name__)

        Returns:
            logging.Logger: Configured logger instance with colored formatting
        """
        logger = logging.getLogger(name)

        # Only add handler if logger doesn't already have handlers
        if not logger.handlers:
            logger.addHandler(self.handler)
            logger.setLevel(self.level)

        return logger

class _ColourFormatter(logging.Formatter):

    # ANSI codes are a bit weird to decipher if you're unfamiliar with them, so here's a refresher
    # It starts off with a format like \x1b[XXXm where XXX is a semicolon separated list of commands
    # The important ones here relate to colour.
    # 30-37 are black, red, green, yellow, blue, magenta, cyan and white in that order
    # 40-47 are the same except for the background
    # 90-97 are the same but "bright" foreground
    # 100-107 are the same as the bright ones but for the background.
    # 1 means bold, 2 means dim, 0 means reset, and 4 means underline.

    LEVEL_COLOURS = [
        (logging.DEBUG, '\x1b[30;1m'),
        (logging.INFO, '\x1b[34;1m'),
        (logging.WARNING, '\x1b[33;1m'),
        (logging.ERROR, '\x1b[31m'),
        (logging.CRITICAL, '\x1b[41m'),
    ]

    FORMATS = {
        level: logging.Formatter(
            f'\x1b[30;1m%(asctime)s\x1b[0m {colour}%(levelname)-8s\x1b[0m \x1b[35m%(name)s\x1b[0m %(message)s',
            '%Y-%m-%d %H:%M:%S',
        )
        for level, colour in LEVEL_COLOURS
    }

    def format(self, record):
        formatter = self.FORMATS.get(record.levelno)
        if formatter is None:
            formatter = self.FORMATS[logging.DEBUG]

        # Override the traceback to always print in red
        if record.exc_info:
            text = formatter.formatException(record.exc_info)
            record.exc_text = f'\x1b[31m{text}\x1b[0m'

        output = formatter.format(record)

        # Remove the cache layer
        record.exc_text = None
        return output

# Create singleton instance
DefaultLoggerFactory = LoggerFactory()