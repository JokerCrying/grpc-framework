import json
from typing import Any, Optional, Type
from .interface import TransportCodec
from ...types import OptionalT, BytesLike, JSONType
from google.protobuf.message import Message
from ...exceptions import GRPCException

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
        if isinstance(obj, BytesLike):
            return obj
        return obj.SerializeToString()


class JSONCodec(TransportCodec):
    def decode(self, data: BytesLike, into: OptionalT = None) -> JSONType:
        return json.loads(data)

    def encode(self, obj: Any) -> BytesLike:
        if isinstance(obj, BytesLike):
            return obj
        return json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


class ORJSONCodec(TransportCodec):
    def __init__(self):
        assert orjson is not None, '`orjson` must be installed to use `ORJSONCodec`'

    def decode(self, data: BytesLike, into: OptionalT = None) -> JSONType:
        return orjson.loads(data)

    def encode(self, obj: Any) -> BytesLike:
        if isinstance(obj, BytesLike):
            return obj
        return orjson.dumps(obj)


class DataclassesCodec(TransportCodec):
    def decode(self, data: BytesLike, into: OptionalT = None) -> JSONType:
        assert into is not None, "DataclassesCodec.decode requires message class via 'into'"
        try:
            data = json.loads(data)
        except:
            raise GRPCException.invalid_argument(f'The data is not json like, can not decode.')
        return data

    def encode(self, obj: JSONType) -> BytesLike:
        if isinstance(obj, BytesLike):
            return obj
        return json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
