from __future__ import annotations

from .application import (
    GRPCFramework, get_current_app
)
from .config import GRPCFrameworkConfig

from .core.adaptor import (
    StreamRequest
)

from .core.request import Request

from .core.response import Response

from .core.enums import Interaction

from .core.middleware import BaseMiddleware

from .core.service import (
    Service, unary_unary, unary_stream, stream_unary, stream_stream, rpc
)

from .core.di.depends import Depends

from .exceptions import GRPCException

from .core.serialization import (
    Serializer,
    TransportCodec,
    ModelConverter,
    JSONCodec,
    ProtobufCodec,
    ORJSONCodec,
    DataclassesCodec,
    ProtobufConverter,
    JsonProtobufConverter,
    JsonConverter,
    DataclassesConverter
)

__version__ = "0.3.0.beta"
__author__ = "surp1us"
__description__ = "gRPC framework for Python"

__all__ = [
    # application
    'GRPCFramework',
    'GRPCFrameworkConfig',
    'get_current_app',

    # request
    'Request',

    # Response
    'Response',

    # enums
    'Interaction',

    # middleware
    'BaseMiddleware',

    # serializer
    'Serializer',
    'TransportCodec',
    'ModelConverter',
    'JSONCodec',
    'ProtobufCodec',
    'ORJSONCodec',
    'DataclassesCodec',
    'ProtobufConverter',
    'JsonProtobufConverter',
    'JsonConverter',
    'DataclassesConverter',

    # Service & grpc endpoint register
    'Service',
    'unary_stream',
    'unary_unary',
    'stream_stream',
    'stream_unary',
    'rpc',

    # adaptor
    'StreamRequest',

    # exception
    'GRPCException',

    # DI
    'Depends'
]
