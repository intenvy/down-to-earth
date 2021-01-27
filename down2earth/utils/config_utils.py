from abc import ABC
from configparser import ConfigParser
from json import dumps
from typing import Dict, Union, Optional


class IFileConfig(ABC, ConfigParser):
    name: str
    __slots__ = '_path', '_encoding'

    def __init__(self, path: str, encoding: str = 'utf8') -> None:
        super().__init__()
        self._path: str = path
        self._encoding = encoding
        self.read(path, encoding=encoding)

    def __str__(self) -> str:
        return dumps(self.as_dict())

    def __repr__(self) -> str:
        return dumps(self.as_dict(), indent=4)

    def save(self) -> None:
        with open(self._path, 'w', encoding=self._encoding) as configfile:
            self.write(configfile)

    def as_dict(self) -> Dict[str, Union[str, Dict[str, str]]]:
        out: Dict[str, Union[str, Dict[str, str]]] = {'name': self.name, 'path': self._path}
        out.update(self._get_values_as_dict())
        return out

    def to_json(self, indent=Optional[int]) -> str:
        return dumps(self.as_dict(), indent=indent)

    def _get_values_as_dict(self) -> Dict[str, Dict[str, str]]:
        out: Dict[str, Dict[str, str]] = {}
        for section in self.sections():
            out[section] = self._get_section(section)
        return out

    def _get_section(self, section: str) -> Dict[str, str]:
        out: Dict[str, str] = {}
        section_content = self.__getitem__(section)
        for key, value in section_content.items():
            out[key] = value
        return out
