from abc import abstractmethod
from typing import Any, Type, TypeVar

from pydantic import BaseConfig
from pydantic.fields import ModelField

from docarray.document.base_node import BaseNode

T = TypeVar('T')


class AbstractType(BaseNode):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    @abstractmethod
    def validate(
        cls: Type[T],
        value: Any,
        field: 'ModelField',
        config: 'BaseConfig',
    ) -> T:
        ...

    @classmethod
    @abstractmethod
    def from_protobuf(cls: Type[T], pb_msg: T) -> T:
        ...