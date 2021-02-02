import asyncio
import math
import time
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager


class IRateLimiter(ABC):

    @abstractmethod
    @asynccontextmanager
    async def throttle(self):
        pass

    @abstractmethod
    async def close(self):
        pass


class TokenBucketRateLimiter(IRateLimiter):
    __slots__ = 'rate_limit', 'tokens_queue', 'tokens_consumer_task', 'semaphore'

    def __init__(self, rate_limit: int, concurrency_limit: int) -> None:
        if not rate_limit or rate_limit < 1:
            raise ValueError('rate limit must be non zero positive number')
        if not concurrency_limit or concurrency_limit < 1:
            raise ValueError('concurrent limit must be non zero positive number')
        self.rate_limit = rate_limit
        self.tokens_queue = asyncio.Queue(rate_limit)
        self.tokens_consumer_task = asyncio.create_task(self._consume_tokens())
        self.semaphore = asyncio.Semaphore(concurrency_limit)

    @asynccontextmanager
    async def throttle(self):
        await self.semaphore.acquire()
        await self._add_token()
        try:
            yield
        finally:
            self.semaphore.release()

    async def close(self) -> None:
        if self.tokens_consumer_task and not self.tokens_consumer_task.cancelled():
            try:
                self.tokens_consumer_task.cancel()
                await self.tokens_consumer_task
            except asyncio.CancelledError:
                # TODO: we ignore this exception but it is good to _log and signal the task was cancelled
                pass
            except Exception as e:
                # TODO: _log here and deal with the exception
                raise

    async def _add_token(self) -> None:
        await self.tokens_queue.put(1)

    async def _consume_tokens(self) -> None:
        try:
            consumption_rate = 1 / self.rate_limit
            last_consumption_time = 0
            while True:
                if self.tokens_queue.empty():
                    await asyncio.sleep(consumption_rate)
                    continue
                current_consumption_time = time.monotonic()
                total_tokens = self.tokens_queue.qsize()
                tokens_to_consume = self._get_tokens_amount_to_consume(
                    consumption_rate,
                    current_consumption_time,
                    last_consumption_time,
                    total_tokens
                )
                for i in range(tokens_to_consume):
                    self.tokens_queue.get_nowait()
                last_consumption_time = time.monotonic()
                await asyncio.sleep(consumption_rate)

        except asyncio.CancelledError:
            # TODO: you can ignore the error here and deal with closing this task later but this is not advised
            raise

        except Exception as e:
            # TODO: do something with the error and re-raise
            raise

    @staticmethod
    def _get_tokens_amount_to_consume(
            consumption_rate: float, current_consumption_time: float, last_consumption_time: float, total_tokens: int
    ) -> int:
        time_from_last_consumption = current_consumption_time - last_consumption_time
        calculated_tokens_to_consume = math.floor(time_from_last_consumption / consumption_rate)
        tokens_to_consume = min(total_tokens, calculated_tokens_to_consume)
        return tokens_to_consume
