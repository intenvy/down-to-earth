from __future__ import annotations
from abc import ABC, abstractmethod
from ssl import SSLContext
from typing import Optional, Dict, Any, Awaitable, Callable

import aiohttp
from aiohttp import ClientSession, ClientResponse as Response, ClientTimeout

from ..enums import RestCallType
from ...utils.serialization_utils import JsonAdaptable
from ...utils.typing_utils import JsonDictionary


def drop_nan_values(params: JsonDictionary) -> None:
    for key, value in params.items():
        if value is None:
            del params[key]


def convert_values_to_str(params: JsonDictionary) -> None:
    for key, value in params.items():
        if value is not None:
            params[key] = str(value)


class IRestRequest(ABC):

    @abstractmethod
    async def fetch(
            self,
            session: Optional[ClientSession] = None,
            ssl_context: Optional[SSLContext] = None,
            callback: Optional[Callable[[IRestRequest, Response], Awaitable[None]]] = None
    ) -> Response:
        pass

    @property
    @abstractmethod
    def domain(self) -> str:
        pass

    @property
    @abstractmethod
    def resource(self) -> str:
        pass

    @property
    @abstractmethod
    def url(self) -> str:
        pass

    @property
    @abstractmethod
    def method(self) -> RestCallType:
        pass

    @property
    @abstractmethod
    def data(self) -> Optional[Dict[str, Any]]:
        pass

    @property
    @abstractmethod
    def headers(self) -> Optional[Dict[str, Any]]:
        pass

    @property
    @abstractmethod
    def params(self) -> Optional[Dict[str, Any]]:
        pass

    @property
    @abstractmethod
    def attempt(self) -> int:
        pass

    @property
    @abstractmethod
    def timeout(self) -> float:
        pass

    @timeout.setter
    @abstractmethod
    def timeout(self, val: float) -> None:
        pass

    @abstractmethod
    def next_attempt(self) -> None:
        pass


class RestRequest(IRestRequest, JsonAdaptable):
    __slots__ = '_method', '_domain', '_resource', '_data', '_headers', '_params', '_attempt', '_timeout', '_url'

    def __init__(
            self,
            method: RestCallType,
            domain: str,
            resource: str,
            timeout: int = 30,
            data: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None
    ) -> None:
        self._method = method
        self._domain = domain
        self._resource = resource
        self._url = f'{domain}/{resource}'
        self._attempt = 1
        self._timeout = ClientTimeout(total=timeout)

        if data is not None:
            drop_nan_values(data)
        self._data = data

        if headers is not None:
            drop_nan_values(headers)
            convert_values_to_str(headers)
        self._headers = headers

        if params is not None:
            drop_nan_values(params)
            convert_values_to_str(params)
        self._params = params

    async def fetch(
            self,
            session: Optional[ClientSession] = None,
            ssl_context: Optional[SSLContext] = None,
            callback: Optional[Callable[[IRestRequest, Response], Awaitable[None]]] = None
    ) -> Response:
        if session is not None:
            call = session.request(
                str(self._method.value),
                self.url,
                json=self._data,
                params=self._params,
                headers=self._headers,
                ssl=ssl_context
            )
        else:
            call = aiohttp.request(
                str(self._method.value),
                self.url,
                json=self._data,
                params=self._params,
                headers=self._headers
            )
        self.next_attempt()
        async with call as response:
            if callback:
                callback(self, response)
            await response.text()
            return response

    @property
    def url(self) -> str:
        return self._url

    @property
    def domain(self) -> str:
        return self._domain

    @property
    def resource(self) -> str:
        return self._resource

    @property
    def method(self) -> RestCallType:
        return self._method

    @property
    def data(self) -> Optional[Dict[str, Any]]:
        return self._data

    @property
    def headers(self) -> Optional[Dict[str, Any]]:
        return self._headers

    @property
    def params(self) -> Optional[Dict[str, Any]]:
        return self._params

    @property
    def attempt(self) -> int:
        return self._attempt

    def next_attempt(self) -> None:
        self._attempt += 1

    @property
    def timeout(self) -> float:
        return self._timeout.total

    @timeout.setter
    def timeout(self, val: float) -> None:
        self._timeout = ClientTimeout(total=val)

    def as_dict(self) -> dict:
        return {
            'url': self.url,
            'method': self._method.value,
            'data': self._data,
            'headers': self._headers,
            'params': self._params,
            'attempt': self._attempt,
        }
