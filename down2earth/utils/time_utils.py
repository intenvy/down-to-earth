import time
from logging import Logger


def get_current_time_ms() -> float:
    return time.time() * 1000


class Timer(object):
    __slots__ = 'name', 'active', 'start_timestamp_ms', 'logger'

    def __init__(self, name: str, logger: Logger, active: bool = True) -> None:
        self.name: str = name
        self.active: bool = active
        self.start_timestamp_ms: float = 0.0
        self.logger = logger

    def __enter__(self) -> None:
        if self.active:
            self.start_timestamp_ms = get_current_time_ms()

    def __exit__(self, type_, value, traceback) -> None:
        if self.active:
            self.logger.debug(
                f'Timer {self.name} finished. Took {round((get_current_time_ms() - self.start_timestamp_ms), 3)} ms.')
