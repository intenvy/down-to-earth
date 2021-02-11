import logging
from logging import Logger
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from enum import Enum

from .serialization_utils import JsonAdaptable


class LogLevel(Enum):
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG


class IMonitorLogger(ABC):

    @abstractmethod
    def log(
            self,
            level: LogLevel,
            msg: str,
            exc_info: Optional[BaseException] = None,
            extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """Logs messages

        This is the main method of the interface, logging messages will be handled here

        :param level: LogLevel
            Log level of the message in str
        :param msg: str
            Message to log
        :param exc_info: Optional[BaseException]
            Exception to log
        :param extra: Optional[Dict[str, Any]]
            extra fields or attributes to log

        :return: None
        """
        pass


class BasicMonitorLogger(IMonitorLogger, JsonAdaptable):

    __slots__ = [
        '_name', '_file_path',
        '_levels', '_stream_log_level', '_file_log_level',
        '_logger',
    ]

    def __init__(
            self,
            name: str,
            path: str,
            stream_log_level: LogLevel,
            file_log_level: LogLevel,
            stream_fmt: str = '[%(asctime)s] [%(name)s] [%(levelname)s] : %(message)s',
            file_fmt: str = '[%(asctime)s] [%(name)s] [%(levelname)s] : %(message)s'
    ) -> None:
        self._logger: Logger = logging.getLogger(name)
        self._file_path = path
        self._stream_log_level: LogLevel = stream_log_level
        self._file_log_level: LogLevel = file_log_level

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(stream_log_level.value)
        stream_handler.setFormatter(logging.Formatter(stream_fmt))

        file_handler = logging.FileHandler(path)
        file_handler.setLevel(file_log_level.value)
        file_handler.setFormatter(logging.Formatter(file_fmt))

        self._logger.addHandler(stream_handler)
        self._logger.addHandler(file_handler)
        self.log(LogLevel.CRITICAL, f'Logger({name}) is initialized')

    def log(
            self,
            level: LogLevel,
            msg: str,
            exc_info: Optional[BaseException] = None,
            extra: Optional[Dict[str, Any]] = None
    ) -> None:
        self._logger.log(level=level.value, msg=msg, exc_info=exc_info, extra=extra)

    def as_dict(self) -> dict:
        return {
            'name': self._logger.name,
            'file_path': self._file_path,
            'stream_log_level': str(self._stream_log_level),
            'file_log_level': str(self._file_log_level)
        }
