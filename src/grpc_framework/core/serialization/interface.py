import abc
from ...types import T, Any, BytesLike, OptionalT, TypeT
from typing import Type

__all__ = [
    'TransportCodec',
    'ModelConverter',
    'Serializer'
]


class TransportCodec(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def decode(self, data: BytesLike, into: OptionalT = None) -> Any:
        """bytes -> transport object (e.g., protobuf.Message or dict)"""
        raise NotImplementedError

    @abc.abstractmethod
    def encode(self, obj: Any) -> BytesLike:
        """transport object -> bytes"""
        raise NotImplementedError


class ModelConverter(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def to_model(self, transport_obj: Any, model_type: TypeT) -> T:
        """transport object -> domain model"""
        raise NotImplementedError

    @abc.abstractmethod
    def from_model(self, model: T) -> Any:
        """domain model -> transport object"""
        raise NotImplementedError


class Serializer:
    def __init__(self, codec: Type[TransportCodec], converter: Type[ModelConverter]):
        self.codec = codec()
        self.converter = converter()

    def deserialize(self, data: bytes, model_type: TypeT) -> T:
        transport_obj = self.codec.decode(data, into=model_type)
        return self.converter.to_model(transport_obj, model_type)

    def serialize(self, model: T) -> bytes:
        transport_obj = self.converter.from_model(model)
        return self.codec.encode(transport_obj)

    def __repr__(self):
        return f'<gRPC Serializer codec={self.codec.__class__.__name__} converter={self.converter.__class__.__name__}>'
