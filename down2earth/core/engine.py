from abc import ABC, abstractmethod
from typing import Dict

from aiohttp import ClientResponse as Response

from .models.request import IRestRequest
from .client import IRestClient


class IEngine(ABC):

    @abstractmethod
    async def fetch(self, request: IRestRequest) -> Response:
        pass


class DownToEarth(IEngine):
    __slots__ = '_client_mapping'

    def __init__(self, mapping: Dict[str, IRestClient]) -> None:
        self._client_mapping = mapping

    async def fetch(self, request: IRestRequest, signed: bool = False) -> Response:
        return await self._client_mapping[request.domain].rest_call(request, signed)
