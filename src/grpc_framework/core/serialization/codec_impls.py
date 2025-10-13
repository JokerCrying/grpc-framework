import json
from typing import Any, Optional, Type
from .interface import TransportCodec
from ...types import OptionalT, BytesLike, JSONType
from google.protobuf.message import Message
from dataclasses import dataclass, is_dataclass, asdict

try:
    import orjson
except ImportError:
    orjson = None


class ProtobufCodec(TransportCodec):
    def decode(self, data: BytesLike, into: Optional[Type[Message]] = None) -> Message:
        assert into is not None, "ProtoCodec.decode requires message class via 'into'"
        msg = into()
        msg.ParseFromString(data)
        return msg

    def encode(self, obj: Message) -> BytesLike:
        return obj.SerializeToString()


class JSONCodec(TransportCodec):
    def decode(self, data: BytesLike, into: OptionalT = None) -> JSONType:
        return json.loads(data)

    def encode(self, obj: Any) -> BytesLike:
        return json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


class ORJSONCodec(TransportCodec):
    def __init__(self):
        assert orjson is not None, '`orjson` must be installed to use `ORJSONCodec`'

    def decode(self, data: BytesLike, into: OptionalT = None) -> JSONType:
        return orjson.loads(data)

    def encode(self, obj: Any) -> BytesLike:
        return orjson.dumps(obj)


class DataclassesCodec(TransportCodec):
    def decode(self, data: BytesLike, into: OptionalT = None) -> Any:
        assert into is not None, "DataclassesCodec.decode requires message class via 'into'"
        try:
            data = json.loads(data)
        except:
            raise ValueError(f'The data is not json like, can not decode.')
        if isinstance(data, list):
            return [into(**i) for i in data]
        elif isinstance(data, dict):
            return into(**data)
        else:
            raise ValueError(f'Can not make a dataclasses instance with {data}.')

    def encode(self, obj: Any) -> BytesLike:
        if not is_dataclass(obj):
            raise ValueError(f'The type {type(obj)} is not dataclasses.')
        return json.dumps(asdict(obj), ensure_ascii=False, separators=(',', ':')).encode('utf-8')
