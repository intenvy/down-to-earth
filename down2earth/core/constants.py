from typing import Set, Type

from aiohttp import (
    ServerTimeoutError,
    ClientOSError, ClientSSLError, ClientHttpProxyError, ClientConnectorCertificateError, ClientProxyConnectionError,
    ContentTypeError, TooManyRedirects
)

DEFAULT_RETRY_STATUS_CODES: Set[int] = {
    500, 502, 503, 504
}

DEFAULT_STOP_STATUS_CODES: Set[int] = {
    400, 401, 402, 403, 404, 405, 406, 407, 412, 413, 411, 410, 409, 415, 501, 505, 507, 508, 510, 511
}

DEFAULT_RETRY_EXCEPTIONS: Set[Type[Exception]] = {
    ServerTimeoutError
}

DEFAULT_STOP_EXCEPTIONS: Set[Type[Exception]] = {
    ClientOSError, ClientSSLError, ClientHttpProxyError, ClientConnectorCertificateError, ClientProxyConnectionError,
    ContentTypeError, TooManyRedirects
}
