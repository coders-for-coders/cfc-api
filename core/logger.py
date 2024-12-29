import logging
import sys
from typing import Optional
from uvicorn.server import logger as uvicorn_logger

class Logger:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance

    def _initialize_logger(self):
        self.logger = logging.getLogger("cfc.api")
        self.logger.setLevel(logging.INFO)
        uvicorn_logger.handlers = self.logger.handlers
        uvicorn_logger.setLevel(self.logger.level)
        uvicorn_logger.name = self.logger.name
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            logging.Formatter(
                '\033[32m%(asctime)s\033[0m | \033[1m%(levelname)s\033[0m | \033[34m%(name)s\033[0m | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        )
        self.logger.addHandler(console_handler)

        file_handler = logging.FileHandler("app.log")
        file_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        )
        self.logger.addHandler(file_handler)

    def info(self, message: str):
        self.logger.info(message)

    def error(self, message: str, exc_info: Optional[bool] = True):
        self.logger.error(message, exc_info=exc_info)

    def warning(self, message: str):
        self.logger.warning(message)

    def debug(self, message: str):
        self.logger.debug(message)

    def critical(self, message: str):
        self.logger.critical(message)