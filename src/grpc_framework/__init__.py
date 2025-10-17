from __future__ import annotations

from .application import (
    GRPCFramework, get_current_app
)
from .config import GRPCFrameworkConfig

from .core.request import Request

from .core.response import Response

from .core.enums import Interaction

from .core.middleware import BaseMiddleware

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
    JsonConverter
)

__version__ = "0.0.1"
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
    'JsonConverter'
]
