from abc import ABC
from configparser import ConfigParser
from typing import Dict, Union
from .serialization_utils import JsonAdaptable


class IFileConfig(ConfigParser, JsonAdaptable):
    name: str
    __slots__ = '_path', '_encoding'

    def __init__(self, path: str, encoding: str = 'utf8') -> None:
        super().__init__()
        self._path: str = path
        self._encoding = encoding
        self.read(path, encoding=encoding)

    def save(self) -> None:
        with open(self._path, 'w', encoding=self._encoding) as configfile:
            self.write(configfile)

    def as_dict(self) -> Dict[str, Union[str, Dict[str, str]]]:
        out: Dict[str, Union[str, Dict[str, str]]] = {'name': self.name, 'path': self._path}
        out.update(self._get_values_as_dict())
        return out

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
