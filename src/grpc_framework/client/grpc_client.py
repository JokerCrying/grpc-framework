import enum
from functools import partial
from typing import Optional, Union, Callable, Any, Tuple, Sequence
from .channel_pool_manager import GRPCChannelPool
from grpc.aio import Metadata

FullNameType = Union[str, Callable]
MetadatumType = Tuple[str, Union[str, bytes]]
MetadataType = Union[Metadata, Sequence[MetadatumType]]


class GRPCRequestType(enum.Enum):
    """grpc request type"""
    unary_unary = 'unary_unary'
    unary_stream = 'unary_stream'
    stream_unary = 'stream_unary'
    stream_stream = 'stream_stream'


class GRPCClient:
    """grpc call client

    Args:
        host: the server host
        port: the server port
        request_serializer: global request serializer, its will use in call_method's param full_name is string type
        response_deserializer: global response deserializer, its will use in call_method's param full_name is string type
        channel_pool_manager: a channel pool type
    """

    def __init__(
            self,
            channel_pool_manager: GRPCChannelPool,
            host: str = 'localhost',
            port: int = 50051,
            request_serializer: Callable = None,
            response_deserializer: Callable = None,
            timeout: Optional[int] = None
    ):
        self.host = host
        self.port = port
        self._address = f'{host}:{port}'
        self._request_serializer = request_serializer
        self._response_deserializer = response_deserializer
        self.channel_pool_manager = channel_pool_manager
        self.timeout = timeout

    def call_method(self,
                    full_name: FullNameType,
                    request_data: Any,
                    metadata: Optional[MetadataType] = None,
                    request_type: Optional[Union[GRPCRequestType, str]] = None,
                    request_serializer: Callable = None,
                    response_deserializer: Callable = None):
        """call a grpc method

        Args:
            full_name: a string type or callable type, its can be a stub.FunctionCall or /package.Service/Method
            metadata: grpc metadata type
            request_data: request data, any of type
            request_type: a grpc request type, it is a required fields when full_name type is string type
            request_serializer: function scope request serializer, its will take precedence over the global request serializer
            response_deserializer:function scope response deserializer, its will take precedence over the global response deserializer
        """
        if request_type:
            if isinstance(request_type, str):
                request_type = GRPCRequestType(request_type)
        if callable(full_name):
            call_func = full_name
        else:
            if not request_type:
                raise ValueError(f'When full_name is of string type, request_type must be passed in')
            original_call_func = self.make_call_func(full_name, request_type)
            req_ser = request_serializer or self._request_serializer
            assert req_ser is not None and callable(
                req_ser), 'request serializer is a required fields when full_name type is string, and its can call.'
            res_des = response_deserializer or self._response_deserializer
            assert res_des is not None and callable(
                res_des), 'response deserializer is a required fields when full_name type is string, and its can call.'
            call_func = partial(original_call_func,
                                request_serializer=req_ser,
                                response_deserializer=res_des)
        return call_func(request_data, timeout=self.timeout, metadata=metadata)

    def make_call_func(self, full_name: str, request_type: GRPCRequestType):
        channel = self.channel_pool_manager.get()
        return getattr(channel, request_type.value)

    unary_unary = partial(call_method, request_type=GRPCRequestType.unary_unary)  # call unary method
    unary_stream = partial(call_method, request_type=GRPCRequestType.unary_stream)  # call unary stream method
    stream_unary = partial(call_method, request_type=GRPCRequestType.stream_unary)  # call stream unary method
    stream_stream = partial(call_method, request_type=GRPCRequestType.stream_stream)  # call stream stream method
