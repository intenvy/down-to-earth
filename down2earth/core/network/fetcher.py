from abc import ABC, abstractmethod
from ssl import SSLContext
from typing import Optional

from aiohttp import ClientResponse as Response, ClientSession

from down2earth.core.models.request import IRestRequest
from down2earth.utils.async_utils import IRateLimiter


class IRestfulFetcher(ABC):

    @abstractmethod
    async def fetch(self, request: IRestRequest) -> Response:
        """Fetch a request for a single time

        :param request: IRestRequest
            request to send to the server
        :return: Response
            Response object returned from server
        """
        pass

    async def close(self) -> None:
        pass


class SessionLessFetcher(IRestfulFetcher, ABC):
    __slots__ = '_ssl_context',

    def __init__(self, ssl_context: Optional[SSLContext] = None) -> None:
        self._ssl_context: Optional[SSLContext] = ssl_context

    async def fetch(self, request: IRestRequest) -> Response:
        return await request.fetch(None, self._ssl_context)


class SessionBasedFetcher(IRestfulFetcher, ABC):
    __slots__ = '_session', '_ssl_context'

    def __init__(self, session: ClientSession, ssl_context: Optional[SSLContext] = None) -> None:
        self._session: ClientSession = session
        self._ssl_context: Optional[SSLContext] = ssl_context

    async def close(self) -> None:
        await self._session.close()

    async def fetch(self, request: IRestRequest) -> Response:
        return await request.fetch(self._session, self._ssl_context)


class RateLimitedFetcher(SessionBasedFetcher, ABC):
    __slots__ = '_rate_limiter',

    def __init__(
            self,
            rate_limiter: IRateLimiter,
            session: Optional[ClientSession] = None,
            ssl_context: Optional[SSLContext] = None
    ) -> None:
        super().__init__(session, ssl_context)
        self._rate_limiter: IRateLimiter = rate_limiter

    @abstractmethod
    async def close(self) -> None:
        await super().close()
        await self._rate_limiter.close()

    async def fetch(self, request: IRestRequest) -> Response:
        async with self._rate_limiter.throttle():
            return await super().fetch(request)
