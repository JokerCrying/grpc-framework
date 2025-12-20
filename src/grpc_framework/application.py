import os
import grpc
import logging
import inspect
import asyncio
import multiprocessing
import grpc.aio as grpc_aio
from .core import Service, RPCFunctionMetadata
from .core.enums import Interaction
from .core.lifecycle import LifecycleManager
from .core.middleware import MiddlewareManager
from .core.interceptors import RequestContextInterceptor
from .core.context import RequestContextManager
from .core.adaptor import GRPCAdaptor
from .core.params import ParamParser
from .core.error_handler import ErrorHandler
from .core.response.response import Response
from .utils import get_logger
from .config import GRPCFrameworkConfig
from .exceptions import GRPCException
from typing import Optional, Type, Union
from contextvars import ContextVar
from grpc_reflection.v1alpha import reflection
from grpc_health.v1 import health_pb2_grpc, health
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


class _EmptyApplication: ...


CURRENT_APP_TYPE = Union['GRPCFramework', Type['_EmptyApplication']]

_current_app: ContextVar[CURRENT_APP_TYPE] = ContextVar('current_app', default=_EmptyApplication)


def get_current_app() -> 'GRPCFramework':
    """get current application"""
    app = _current_app.get()
    if app is _EmptyApplication:
        raise RuntimeError('application has not ready for start or init, check it please.')
    return app


class GRPCFramework:
    """easy grpc apis framework

    a pythonic application to make a grpc project.

    Args:
        config: application config
    """

    def __init__(
            self,
            config: Optional[GRPCFrameworkConfig] = None
    ):
        # Removing that definition will be fetched when the worker starts
        # self.loop = asyncio.get_event_loop()
        self.logger = get_logger('grpc-framework', logging.INFO)
        self.config = config or GRPCFrameworkConfig()
        self._services = {
            self.config.app_service_name: {}
        }
        # make interceptors
        self._server_interceptors = [
            RequestContextInterceptor(self)
        ]
        if self.config.interceptors is not None:
            self._server_interceptors.extend(self.config.interceptors)
        # make grpc aio server
        self._server: Optional[grpc_aio.Server] = None
        # temporarily rpc stub
        self._pending_rpc_stub = []
        # lifecycle manager
        self._lifecycle_manager = LifecycleManager(None)
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
        self.render_content = self._serializer.serialize
        self.load_content = self._serializer.deserialize
        # request hook
        self._request_context_manager = RequestContextManager(self)
        self.before_request = self._request_context_manager.before_request
        self.after_request = self._request_context_manager.after_request
        self.start_request_context = self._request_context_manager.context
        # adaptor
        self._adaptor = GRPCAdaptor(self)
        # error handler
        self._error_handler = ErrorHandler(self)
        self.add_error_handler = self._error_handler.add_error_handler
        # plugin
        self.plugins = {}  # For subsequent support plugins
        # set context var
        _current_app.set(self)

    def method(self, request_interaction: Interaction, response_interaction: Interaction):
        """register an endpoint to root service

        :param request_interaction: Interaction type, unary or stream
        :param response_interaction: Interaction type, unary or stream
        """

        def decorator(func):
            self._services[self.config.app_service_name][func.__name__] = RPCFunctionMetadata(
                handler=func,
                request_interaction=request_interaction,
                response_interaction=response_interaction,
                rpc_service=None,
                return_param_info=ParamParser.parse_return_type(func),
                input_param_info=ParamParser.parse_input_params(func)
            )
            return func

        return decorator

    def unary_unary(self, func):
        """register a unary_unary endpoint to root service"""
        return self.method(Interaction.unary, Interaction.unary)(func)

    def unary_stream(self, func):
        """register a unary_stream endpoint to root service"""
        return self.method(Interaction.unary, Interaction.stream)(func)

    def stream_unary(self, func):
        """register a stream_unary endpoint to root service"""
        return self.method(Interaction.stream, Interaction.unary)(func)

    def stream_stream(self, func):
        """register a stream_stream endpoint to root service"""
        return self.method(Interaction.stream, Interaction.stream)(func)

    def add_service(self, svc: Union[Type[Service], Service]):
        """add a function based view or class based view to service

        :param svc: cbv or fbv service
        :return: None
        """
        if inspect.isclass(svc) and issubclass(svc, Service):
            # cbv
            methods = svc.collect_rpc_methods()
            method_name = svc.__name__
        elif isinstance(svc, Service):
            # fbv
            methods = svc.methods
            method_name = svc.service_name
        else:
            raise TypeError(f'got an error type when add grpc service, type is {type(svc)}')
        self._services[method_name] = methods

    def load_rpc_stub(self, impl, add_service_func):
        """load a proto rpc service to server, its can compatibility old project in
        your team, asynchronous encoding is recommended

        warning: grpc framework will no longer take over the endpoint behavior, so request context like Request Response
            can not be use.

        :param impl: grpc impl servicer
        :param add_service_func: python protoc will generate a function to add servicer to server, the app
            will add impl to server
        :return: None
        """
        self._pending_rpc_stub.append((impl, add_service_func))

    def _register_legacy_stubs(self, _):
        for impl, add_service_fun in self._pending_rpc_stub:
            add_service_fun(impl(), self._server)

    async def dispatch(self, request, context):
        """call middleware chain when a request context"""
        return await self._middleware_manager.dispatch(request, context)

    def find_endpoint(self, _: str, svc: str, method: str) -> RPCFunctionMetadata:
        """find grpc endpoint

        :param _: grpc package
        :param svc: service name
        :param method: method name
        :return: a grpc function metadata, its store endpoint metadata
        """
        service_metas = self._services.get(svc)
        if service_metas is None:
            raise RuntimeError(f'unknown {svc} in registered services.')
        method_meta = service_metas.get(method)
        if method_meta is None:
            raise RuntimeError(f'unknown {method_meta} in registered services.')
        return method_meta

    def run(self):
        if self.config.workers <= 1:
            self._run_single_worker()
            return
        self.logger.info(f'Starting Server with {self.config.workers} workers.')
        processes = []
        try:
            for _ in range(self.config.workers):
                p = multiprocessing.Process(
                    target=self._run_single_worker,
                    args=()
                )
                p.start()
                processes.append(p)
            for p in processes:
                p.join()
        except KeyboardInterrupt:
            self.logger.info('- Shutting down workers...')
            for p in processes:
                if p.is_alive():
                    p.terminate()
            for p in processes:
                p.join()
            self.logger.info('- All workers stopped.')

    async def _start(self):
        """call application context"""
        async with self._lifecycle_manager.context(self):
            pass

    def _register_services_in_service(self, _):
        """register application services to server"""
        for svc_name, data in self._services.items():
            rpc_method_handlers = {}
            for method_name, metadata in data.items():
                request_interaction = metadata['request_interaction']
                response_interaction = metadata['response_interaction']
                request_mode = '_'.join([request_interaction.value, response_interaction.value])
                if request_mode == 'unary_unary':
                    use_grpc_handler_func = 'unary_unary_rpc_method_handler'
                    use_adaptor_wrap = 'wrap_unary_unary_handler'
                elif request_mode == 'unary_stream':
                    use_grpc_handler_func = 'unary_stream_rpc_method_handler'
                    use_adaptor_wrap = 'wrap_unary_stream_handler'
                elif request_mode == 'stream_unary':
                    use_grpc_handler_func = 'stream_unary_rpc_method_handler'
                    use_adaptor_wrap = 'wrap_stream_unary_handler'
                elif request_mode == 'stream_stream':
                    use_grpc_handler_func = 'stream_stream_rpc_method_handler'
                    use_adaptor_wrap = 'wrap_stream_stream_handler'
                else:
                    raise TypeError(f'got an unknown endpoint type, it is {request_mode}')
                rpc_method_handlers[method_name] = getattr(grpc, use_grpc_handler_func)(
                    behavior=getattr(self._adaptor, use_adaptor_wrap)(metadata)
                )
                service_name = f'{self.config.package}.{svc_name}'
                generic_handler = grpc.method_handlers_generic_handler(
                    service_name, rpc_method_handlers
                )
                self._server.add_generic_rpc_handlers((generic_handler,))
                self._server.add_registered_method_handlers(service_name, rpc_method_handlers)

    def _enable_reflection(self, _):
        """enable grpc reflection if config reflection"""
        if self.config.reflection:
            for svc_name, _ in self._services.items():
                service_name = f'{self.config.package}.{svc_name}'
                service_names = (
                    service_name,
                    reflection.SERVICE_NAME
                )
                reflection.enable_server_reflection(service_names, self._server)

    def _add_health_check(self, _):
        """add grpc standard health check"""
        if self.config.add_health_check:
            self.load_rpc_stub(health.HealthServicer, health_pb2_grpc.add_HealthServicer_to_server)

    async def _server_start(self, _):
        """start server in application context last step"""
        run_endpoint = f'{self.config.host}:{self.config.port}'
        self._server.add_insecure_port(run_endpoint)
        await self._server.start()
        self.logger.info(f'- The Server `{self.config.name}` (PID: {os.getpid()}) Running in {run_endpoint}')
        try:
            await self._server.wait_for_termination()
        except asyncio.CancelledError:
            pass
        finally:
            try:
                await self._server.stop(None)
            except asyncio.CancelledError:
                pass

    async def _init_error_handler(self, _):
        @self.add_error_handler(GRPCException)
        async def handler(request, error):
            return self._error_handler.grpc_error_handler(request, error)

    def _log_request(self, response: Response):
        """log request in request context last step"""
        if response.status_code is not grpc.StatusCode.OK:
            logger_level = 'error'
        else:
            logger_level = 'info'
        getattr(self.logger, logger_level)(
            f'Call method code={response.status_code}: /{response.package}.{response.service_name}/{response.method_name}')

    def _build_runtime(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        _current_app.set(self)
        options = list(self.config.grpc_options or [])
        if self.config.workers > 1:
            for opt in options:
                if opt[0] == 'grpc.so_reuseport':
                    if opt[1] != 1:
                        raise ValueError('When multi-worker is enabled, set `grpc.so_reuseport` to 1.')
                    break
            else:
                options.append(('grpc.so_reuseport', 1))
        runtime_executor = self._make_execute()
        self._lifecycle_manager.update_executor(runtime_executor)
        self._lifecycle_manager.set_loop(self.loop)
        self._request_context_manager.init_s2a(runtime_executor)
        self._adaptor.init_s2a(runtime_executor)
        self._error_handler.init_s2a(runtime_executor)
        self._server = grpc_aio.server(
            migration_thread_pool=runtime_executor,
            handlers=self.config.grpc_handlers,
            interceptors=self._server_interceptors,  # 使用之前存好的拦截器列表
            options=options,
            maximum_concurrent_rpcs=self.config.maximum_concurrent_rpc,
            compression=self.config.grpc_compression
        )

    def _run_single_worker(self):
        self._build_runtime()
        self._lifecycle_manager.on_startup(self._register_services_in_service)
        self._lifecycle_manager.on_startup(self._register_legacy_stubs)
        self._lifecycle_manager.on_startup(self._enable_reflection)
        self._lifecycle_manager.on_startup(self._add_health_check)
        self._lifecycle_manager.on_startup(self._init_error_handler)
        self._lifecycle_manager.on_startup(self._server_start, -1)
        self._request_context_manager.after_request(self._log_request, -1)
        main_task = self.loop.create_task(self._start())
        try:
            self.logger.info(f'Worker process [{os.getpid()}] started.')
            self.loop.run_until_complete(main_task)
        except (KeyboardInterrupt, asyncio.CancelledError):
            # 子进程只需要处理任务取消，不需要打印 "Shutting down" (由主进程统一管理日志更好)
            pass
        finally:
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.close()

    def _make_execute(self):
        if self.config.executor_type == 'threading':
            executor_type = ThreadPoolExecutor
        elif self.config.executor_type == 'process':
            executor_type = ProcessPoolExecutor
        else:
            raise ValueError('The config `executor_type` only in value range `threading` or `process`.')
        return executor_type(max_workers=self.config.execute_workers)

    def __getstate__(self):
        state = self.__dict__.copy()
        if 'logger' in state:
            state.pop('logger')
        return state

    def __setstate__(self, state):
        state['logger'] = get_logger('grpc-framework', logging.INFO)
        self.__dict__.update(state)

    def __repr__(self):
        return f'<gRPC Framework name={self.config.name}>'
