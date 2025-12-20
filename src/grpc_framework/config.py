import os
import grpc
import importlib
from dataclasses import dataclass
from typing import Type, Union, Optional, Sequence, Any, Literal
from grpc.aio import ChannelArgumentType
from .core import Serializer, ProtobufCodec, ProtobufConverter, TransportCodec, ModelConverter
from .types import FilePath, ModulePath
from .utils import add_config_parser, parse_config, CONFIG_PARSER_TYPE, ConfigParserOptions


@dataclass
class GRPCFrameworkConfig:
    """gRPC Framework Global Config

    Args:
        package: grpc package, it is a requireable arg, can not be 'grpc'
        name: application name
        version: application version
        host: application run host
        port: application run port
        serializer: global serializer, it is responsible for the format compilation in the request
        codec: global codec, it is responsible translate transport data to message type or translate message type to transport data
        converter: global codec, it is responsible translate message type to domain model or translate domain model to message type
        reflection: is a reflection interface needed
        add_health_check: is add standard grpc health check service needed
        app_service_name: set a service name for use app fbv mode.
        executor: global thread pool executor, it will also be applied in the `migration_thread_pool` parameter of `grpc.aio.server`
        grpc_handlers: An optional list of GenericRpcHandlers used for executing RPCs.
            More handlers may be added by calling add_generic_rpc_handlers any time
            before the server is started.
        interceptors: An optional list of ServerInterceptor objects that observe
            and optionally manipulate the incoming RPCs before handing them over to
            handlers. The interceptors are given control in the order they are
            specified. This is an EXPERIMENTAL API.
        grpc_options: An optional list of key-value pairs (:term:`channel_arguments` in gRPC runtime)
            to configure the channel.
        maximum_concurrent_rpc: The maximum number of concurrent RPCs this server
            will service before returning RESOURCE_EXHAUSTED status, or None to
            indicate no limit.
        grpc_compression: An element of grpc.compression, e.g.
            grpc.compression.Gzip. This compression algorithm will be used for the
            lifetime of the server unless overridden by set_compression.
        workers: Start multiple grpc services,
            and the configuration of 'grpc.so_reuseport=1' will be added to the 'grpc_options' by default,
            warning: this feature is not available in Windows!
    """

    package: str = 'grpc'
    name: str = 'grpc-framework'
    version: str = '0.0.0'
    host: str = 'localhost'
    port: int = 50051
    serializer: Type[Serializer] = Serializer
    codec: Type[TransportCodec] = ProtobufCodec
    converter: Type[ModelConverter] = ProtobufConverter
    reflection: bool = False
    add_health_check: bool = False
    app_service_name: str = 'RootService'
    executor_type: Literal['threading', 'process'] = 'threading'
    execute_workers: int = os.cpu_count() * 2 - 1
    grpc_handlers: Optional[Sequence[grpc.GenericRpcHandler]] = None
    interceptors: Optional[Sequence[grpc.ServerInterceptor]] = None
    grpc_options: Optional[ChannelArgumentType] = None
    maximum_concurrent_rpc: Optional[int] = None
    grpc_compression: Optional[grpc.Compression] = None
    workers: int = 1

    @classmethod
    def from_file(cls, filename: FilePath, options: ConfigParserOptions = None) -> 'GRPCFrameworkConfig':
        """read config from file"""
        options = options or ConfigParserOptions(
            ini_root_name='root'
        )
        filetype = filename.split('.')[-1]
        config = parse_config(filetype, filename, options)
        annotations = cls.__annotations__.keys()
        return cls(**{
            k: v
            for k, v in config.items()
            if k in annotations
        })

    @classmethod
    def from_module(cls, module_path: ModulePath, package: str = None) -> 'GRPCFrameworkConfig':
        """read config from python module"""
        module = importlib.import_module(module_path, package)
        annotations = cls.__annotations__.keys()
        return cls(**{
            k: getattr(module, k, None)
            for k in dir(module)
            if not k.startswith('__') and
               getattr(module, k, None) is not None and
               k in annotations
        })

    @staticmethod
    def add_config_parser(filetype: str, parser: CONFIG_PARSER_TYPE):
        """add a config parser to support filetype"""
        add_config_parser(filetype, parser)

    def __post_init__(self):
        if self.package == 'grpc':
            raise ValueError("Can not be 'grpc' value when initialize GRPCFrameworkConfig, set a other value please.")
        if self.workers < 1:
            raise ValueError("The number of workers started is at least 1.")
        if self.execute_workers < 1:
            raise ValueError("The number of execute_workers started is at least 1.")
