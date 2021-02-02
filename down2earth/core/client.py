import json
from abc import ABC, abstractmethod
from typing import Dict, Any
from typing import Optional, Union

from aiohttp import ClientResponse as Response, ClientSession
from multidict import CIMultiDictProxy

from .enums import RestCallType
from .models.request import IRestRequest
from .mechanisms.fetch import IFetchMechanism
from ..errors.fetching_errors import FetchMechanismFailed
from ..utils.typing_utils import StringMapping, Json, JsonDictionary
from ..utils.config_utils import IFileConfig


def clean_request_params(params: JsonDictionary) -> StringMapping:
    clean_params = {}
    for key, value in params.items():
        if value is not None:
            clean_params[key] = str(value)
    return clean_params


async def deserialize_response(response: Response) -> Optional[Json]:
    content = await response.text()
    if len(content) > 0:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return dict(raw=content)


class IRestClient(ABC):

    @abstractmethod
    @property
    def fetch_mechanism(self) -> IFetchMechanism:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass

    def _sign_payload(self, request: IRestRequest) -> None:
        pass

    def _on_response_received(self, request: IRestRequest, response: Response) -> None:
        pass

    def _on_mechanism_failure(self, request: IRestRequest) -> None:
        pass

    async def _rest_call(self, request: IRestRequest, signed: bool = False) -> Response:
        mechanism = self.fetch_mechanism
        if signed:
            self._sign_payload(request)
        try:
            response = await mechanism.fetch(request)
            self._on_response_received(request, response)
            return response
        except FetchMechanismFailed as e:
            self._on_mechanism_failure(request)


class RestClient(IRestClient):

    __slots__ = '_fetch_mechanism'

    def __init__(self, mechanism: IFetchMechanism):
        self._fetch_mechanism: IFetchMechanism = mechanism

    @property
    def fetch_mechanism(self) -> IFetchMechanism:
        return self._fetch_mechanism

    async def close(self) -> None:
        await self._fetch_mechanism.close()

    def _on_mechanism_failure(self, request: IRestRequest) -> None:
        print(request.__repr__())
        # TODO log

    def _on_response_received(self, request: IRestRequest, response: Response) -> None:
        print('response received')
        # TODO log


"""
class IRestClient(ABC):

    def __init__(self, api_trace_log: bool = False, ssl_context: ssl.SSLContext = None) -> None:
        self.api_trace_log = api_trace_log
        self.rest_session = None
        self.subscription_sets = []

        if ssl_context is not None:
            self.ssl_context = ssl_context
        else:
            self.ssl_context = ssl.create_default_context()

    @abstractmethod
    def _get_rest_api_uri(self, resource: str) -> str:
        pass

    @abstractmethod
    def _sign_payload(self,
                      rest_call_type: RestCallType,
                      resource: str,
                      data: Optional[dict] = None,
                      params: Optional[dict] = None,
                      headers: Optional[dict] = None) -> None:
        pass

    @abstractmethod
    def _on_response_received(self,
                                  status_code: int,
                                  headers: CIMultiDictProxy[str],
                                  body: Optional[dict] = None) -> None:
        pass

    def rest_session(self) -> aiohttp.ClientSession:
        pass

    async def close(self) -> None:
        session = self.rest_session()
        if session is not None:
            await session.close()

    async def _fetch(self,
                     rest_call_type: RestCallType,
                     resource: str,
                     data: Optional[dict] = None,
                     params: Optional[dict] = None,
                     headers: Optional[dict] = None) -> aiohttp.ClientResponse:
        call = self.rest_session().request(
            rest_call_type.value,
            self._get_rest_api_uri(resource),
            json=data,
            params=params,
            headers=headers,
            ssl=self.ssl_context
        )
        async with call as response:
            status_code = response.status
            if 300 > status_code >= 200:
                return response

    async def _make_rest_call(self, rest_call_type: RestCallType, resource: str, data: dict = None,
                              params: dict = None, headers: dict = None, signed: bool = False) -> dict:
        # ensure headers is always a valid object
        if headers is None:
            headers = {}

        # add signature into the parameters
        if signed:
            self._sign_payload(rest_call_type, resource, data, params, headers)

        # fetch the response
        response = await self._fetch(rest_call_type, resource, data=data, params=params, headers=headers)
        status_code = response.status
        headers = response.headers
        body = await response.text()

        if len(body) > 0:
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                body = dict(raw=body)
        self._on_response_received(status_code, headers, body)
        return dict(status_code=status_code, headers=headers, response=body)

    def rest_session(self) -> aiohttp.ClientSession:
        if self.rest_session is not None:
            return self.rest_session

        if self.api_trace_log:
            trace_config = aiohttp.TraceConfig()
            trace_config.on_request_start.append(CryptoXLibClient._on_request_start)
            trace_config.on_request_end.append(CryptoXLibClient._on_request_end)
            trace_configs = [trace_config]
        else:
            trace_configs = None

        self.rest_session = aiohttp.ClientSession(trace_configs=trace_configs)

        return self.rest_session

    @staticmethod
    def clean_request_params(params: dict) -> dict:
        clean_params = {}
        for key, value in params.items():
            if value is not None:
                clean_params[key] = str(value)

        return clean_params

    @staticmethod
    async def _on_request_start(session, trace_config_ctx, params) -> None:
        LOG.debug(f'> Context: {trace_config_ctx}')
        LOG.debug(f'> Params: {params}')

    @staticmethod
    async def _on_request_end(session, trace_config_ctx, params) -> None:
        LOG.debug(f'< Context: {trace_config_ctx}')
        LOG.debug(f'< Params: {params}')

    @staticmethod
    def _get_current_timestamp_ms() -> int:
        return int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000)

    @staticmethod
    def _get_unix_timestamp_ns() -> int:
        return int(time.time_ns() * 10 ** 9)
"""
