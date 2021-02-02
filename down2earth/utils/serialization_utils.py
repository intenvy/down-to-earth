from abc import ABC, abstractmethod
from json import dumps
from typing import Optional


class JsonAdaptable(ABC):

    @abstractmethod
    def as_dict(self) -> dict:
        pass

    def to_json(self, indent: Optional[int] = None) -> str:
        return dumps(self.as_dict(), indent=indent)

    def __str__(self):
        return self.to_json()

    def __repr__(self):
        return self.to_json(indent=4)
