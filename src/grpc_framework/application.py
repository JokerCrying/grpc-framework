import inspect
import grpc.aio as grpc_aio
from .core import Service, RPCFunctionMetadata
from .core.enums import Interaction
from .core.lifecycle import LifecycleManager
from .core.middleware import MiddlewareManager
from .config import GRPCFrameworkConfig
from typing import Optional, Type, Union, Callable


class GRPCFramework:
    def __init__(
            self,
            config: Optional[GRPCFrameworkConfig] = None
    ):
        self.config = config or GRPCFrameworkConfig()
        self._services = {
            self.config.app_service_name: {}
        }
        self._server = grpc_aio.server(
            migration_thread_pool=self.config.executor,
            handlers=self.config.grpc_handlers,
            interceptors=self.config.interceptors,
            options=self.config.grpc_options,
            maximum_concurrent_rpcs=self.config.maximum_concurrent_rpc,
            compression=self.config.grpc_compression
        )
        # lifecycle manager
        self._lifecycle_manager = LifecycleManager(self.config.executor)
        self.on_startup = self._lifecycle_manager.on_startup
        self.on_shutdown = self._lifecycle_manager.on_shutdown
        self.lifecycle = self._lifecycle_manager.lifecycle
        # middleware
        self._middleware_manager = MiddlewareManager(self)
        self.add_middleware = self._middleware_manager.add_middleware
        # serialization
        self._serializer = self.config.serializer(
            codec=self.config.codec,
            converter=self.config.converter
        )

    def method(self, request_interaction: Interaction, response_interaction: Interaction):
        def decorator(func):
            self._services[self.config.app_service_name][func.__name__] = RPCFunctionMetadata(
                handler=func,
                request_interaction=request_interaction,
                response_interaction=response_interaction
            )
            return func

        return decorator

    def add_service(self, svc: Union[Type[Service], Service]):
        if inspect.isclass(svc) and issubclass(svc, Service):
            # cbv
            methods = svc.collect_rpc_methods()
            method_name = svc.__class__.__name__
        elif isinstance(svc, Service):
            # fbv
            methods = svc.methods
            method_name = svc.service_name
        else:
            raise TypeError(f'got an error type when add grpc service, type is {type(svc)}')
        self._services[method_name] = methods

    async def dispatch(self, request, context):
        return await self._middleware_manager.dispatch(request, context)

    def find_endpoint(self, pkg: str, svc: str, method: str) -> RPCFunctionMetadata:
        service_metas = self._services.get(svc)
        if service_metas is None:
            raise RuntimeError(f'unknown {svc} in registered services.')
        method_meta = service_metas.get(method)
        if method_meta is None:
            raise RuntimeError(f'unknown {method_meta} in registered services.')
        return method_meta

    def __repr__(self):
        return f'<gRPC Framework name={self.config.name}>'
