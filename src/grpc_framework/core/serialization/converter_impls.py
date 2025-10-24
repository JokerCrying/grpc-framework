import json
from typing import Type, List, Union, Dict, Any
from .interface import ModelConverter
from ...types import JSONType, T, TypeT
from google.protobuf.message import Message
from google.protobuf.json_format import ParseDict, MessageToDict
from dataclasses import is_dataclass, asdict


class JsonProtobufConverter(ModelConverter):
    """bidirectional converter：JSON <-> Protocol Buffers"""

    def to_model(self, transport_obj: JSONType, model_type: Type[Message]) -> Union[Message, List[Message]]:
        """Convert JSON data to protobuf message(s)"""
        if isinstance(transport_obj, list):
            return [self._parse_single(item, model_type) for item in transport_obj]
        elif isinstance(transport_obj, dict):
            return self._parse_single(transport_obj, model_type)
        else:
            raise ValueError(f'Cannot convert JSON primitive {type(transport_obj)} to protobuf message')

    def from_model(self, protobuf_model: Union[Message, List[Message]]) -> JSONType:
        """Convert protobuf message(s) to JSON data"""
        if isinstance(protobuf_model, list):
            return [MessageToDict(msg, preserving_proto_field_name=True) for msg in protobuf_model]
        elif hasattr(protobuf_model, '__class__') and issubclass(protobuf_model.__class__, Message):
            return MessageToDict(protobuf_model, preserving_proto_field_name=True)
        else:
            raise TypeError(f'Expected protobuf message, got {type(protobuf_model)}')

    @staticmethod
    def _parse_single(data: Dict[str, Any], model_type: Type[Message]) -> Message:
        """Helper method to parse single JSON object to protobuf message"""
        if not isinstance(data, dict):
            raise TypeError(f'Expected dict for single object, got {type(data)}')
        # 创建空的protobuf实例并填充数据
        return ParseDict(data, model_type())


class DataclassesConverter(ModelConverter):
    def to_model(self, transport_obj: JSONType, model_type: TypeT) -> T:
        if isinstance(transport_obj, list):
            return [self._parse_single(i, model_type) for i in transport_obj]
        elif isinstance(transport_obj, dict):
            return self._parse_single(transport_obj, model_type)
        raise ValueError(f'Cannot convert JSON primitive {type(transport_obj)} to dataclass instance')

    def from_model(self, model: T) -> Any:
        if isinstance(model, list):
            return [asdict(i) for i in model]
        elif is_dataclass(model):
            return asdict(model)
        raise TypeError(f'Expected dataclass instance, got {type(model)}')

    @staticmethod
    def _parse_single(data: Dict[str, Any], model_type: TypeT) -> TypeT:
        """Helper method to parse single JSON object to dataclass instance"""
        if not isinstance(data, dict):
            raise TypeError(f'Expected dict for single object, got {type(data)}')
        # 创建空的protobuf实例并填充数据
        return model_type(**data)  # Type: Message


class JsonConverter(ModelConverter):
    def to_model(self, transport_obj: Any, model_type: JSONType) -> JSONType:
        return json.loads(transport_obj)  # type: JSONType

    def from_model(self, model: JSONType) -> JSONType:
        return json.dumps(model, ensure_ascii=False, separators=(',', ':'))  # type: Union[Dict, List]


class ProtobufConverter(ModelConverter):
    def to_model(self, transport_obj: Any, model_type: Type[Message]) -> Message:
        return model_type.FromString(transport_obj)  # type: Message

    def from_model(self, model: Message) -> Any:
        return model.SerializeToString()  # type: bytes
