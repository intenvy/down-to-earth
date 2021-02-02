from typing import Optional

from down2earth.utils.serialization_utils import JsonAdaptable


class FetchMechanismError(Exception):
    pass


class FetchMechanismFailed(FetchMechanismError, JsonAdaptable):
    __slots__ = '_message', '_response_status_code', '_exception'

    def __init__(
            self,
            message: str,
            response_status_code: Optional[int] = None,
            exception: Optional[Exception] = None
    ) -> None:
        super().__init__()
        self._message: str = message
        self._response_status_code: Optional[int] = response_status_code
        self._exception: Optional[exception] = exception

    def as_dict(self) -> dict:
        out = {'message': self._message}
        if self._response_status_code is not None:
            out['response_status_code'] = self._response_status_code
        if self._exception is not None:
            out['exception'] = str(self._exception).strip().replace('\n', ' ')
        return out
