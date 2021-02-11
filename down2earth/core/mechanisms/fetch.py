from abc import ABC, abstractmethod
from typing import Optional, Iterable, Set, Type

from aiohttp import ClientResponse as Response, ServerTimeoutError

from down2earth.core.models.request import IRestRequest
from down2earth.core.network.fetcher import IRestfulFetcher
from down2earth.errors import FetchMechanismFailed
from ..constants import (
    DEFAULT_RETRY_EXCEPTIONS, DEFAULT_STOP_EXCEPTIONS,
    DEFAULT_RETRY_STATUS_CODES, DEFAULT_STOP_STATUS_CODES
)
from ...utils.typing_utils import NumericType


class IFetchMechanism(ABC):

    @abstractmethod
    async def fetch(self, request: IRestRequest) -> Response:
        """Fetch a request through a mechanism

        This facade layer provides the core functionality of this interface

        :param request: IRestRequest
            The request to send
        :return: Response
            Final response object returned from mechanism
        """
        pass

    async def close(self) -> None:
        pass


class ICyclicFetchMechanism(IFetchMechanism, ABC):

    @abstractmethod
    def on_cycle_state(
            self,
            request: IRestRequest,
            response: Optional[Response] = None,
            exception: Optional[Exception] = None
    ) -> None:
        """Acts based on different states of the cycle

        :param request: IRestRequest
            The request object
        :param response: Optional[Response]
            Response received from server
        :param exception: Optional[Exception]
            The exception occurred while requesting
        :return: None

        :raises: FetchMechanismFailed
            when the mechanism has failed for any reason
        """
        pass

    @abstractmethod
    def get_sleep_time(
            self,
            request: IRestRequest,
            response: Optional[Response] = None,
            exception: Optional[Exception] = None
    ) -> float:
        """Gets the amount of time to sleep until next retry

        :param request: IRestRequest
            The request object
        :param response: Optional[Response]
            Response received from server
        :param exception: Optional[Exception]
            The exception occurred while requesting
        :return: float
            Amount of time to sleep in seconds
        """
        pass


class ConstantTimeRetry(ICyclicFetchMechanism, ABC):
    __slots__ = '_sleep_time',

    def __init__(self, sleep_time: NumericType) -> None:
        self._sleep_time: NumericType = sleep_time

    def get_sleep_time(
            self,
            request: IRestRequest,
            response: Optional[Response] = None,
            exception: Optional[Exception] = None
    ) -> float:
        return self._sleep_time


class ExponentialTimeRetry(ICyclicFetchMechanism, ABC):
    __slots__ = '_first_sleep_time', '_exponent'

    def __init__(self, first_sleep: NumericType, exponent: NumericType) -> None:
        self._first_sleep_time = first_sleep
        self._exponent = exponent

    def get_sleep_time(
            self,
            request: IRestRequest,
            response: Optional[Response] = None,
            exception: Optional[Exception] = None
    ) -> float:
        if type(exception) is ServerTimeoutError:
            return self._first_sleep_time * self._exponent ** request.attempt
        return self._first_sleep_time


class GentleMechanism(ExponentialTimeRetry):
    __slots__ = [
        '_fetcher', '_max_attempts',
        '_retry_exceptions', '_stop_exceptions',
        '_retry_status_codes', '_stop_status_codes',
    ]

    def __init__(
            self,
            fetcher: IRestfulFetcher,
            first_sleep: NumericType,
            exponent: NumericType,
            max_attempts: int,
            retry_status_codes: Optional[Iterable[int]] = None,
            stop_status_codes: Optional[Iterable[int]] = None,
            retry_exceptions: Optional[Iterable[Type[Exception]]] = None,
            stop_exceptions: Optional[Iterable[Type[Exception]]] = None
    ) -> None:
        super().__init__(first_sleep, exponent)
        self._fetcher: IRestfulFetcher = fetcher
        self._max_attempts: int = max_attempts
        self._retry_status_codes: Set[int] = set(retry_status_codes) if retry_status_codes is not None \
            else DEFAULT_RETRY_STATUS_CODES
        self._stop_status_codes: Set[int] = set(stop_status_codes) if stop_status_codes is not None \
            else DEFAULT_STOP_STATUS_CODES
        self._retry_exceptions: Set[Type[Exception]] = set(retry_exceptions) if retry_exceptions is not None \
            else DEFAULT_RETRY_EXCEPTIONS
        self._stop_exceptions: Set[Type[Exception]] = set(stop_exceptions) if stop_exceptions is not None \
            else DEFAULT_STOP_EXCEPTIONS

    def on_cycle_state(
            self,
            request: IRestRequest,
            response: Optional[Response] = None,
            exception: Optional[Exception] = None
    ) -> None:
        if response is not None:
            status_code = response.status
            if 200 <= status_code < 300:
                return
            if status_code in self._stop_status_codes:
                raise FetchMechanismFailed('Stop status codes are hit', status_code, exception)
            if status_code not in self._retry_status_codes:
                raise FetchMechanismFailed('Status code not in retry status codes', status_code, exception)

        if exception is not None:
            exc_type = type(exception)
            if exc_type in self._stop_exceptions:
                raise FetchMechanismFailed('Stop exceptions are hit', exception=exception)
            if exc_type not in self._retry_exceptions:
                raise FetchMechanismFailed('Exception type not in retry exceptions', exception=exception)

        if request.attempt > self._max_attempts:
            raise FetchMechanismFailed('Maximum attempts reached', response.status, exception)

    async def fetch(self, request: IRestRequest) -> Response:
        for attempt in range(request.attempt, self._max_attempts + 1):
            try:
                response = await self._fetcher.fetch(request)
                self.on_cycle_state(request, response=response)
                return response

            except FetchMechanismFailed as e:
                raise

            except Exception as e:
                self.on_cycle_state(request, exception=e)

    async def close(self) -> None:
        await self._fetcher.close()
