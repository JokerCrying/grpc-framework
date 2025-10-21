import inspect
import traceback
from functools import partial
from typing import TYPE_CHECKING, Any, Callable
from grpc.aio import ServicerContext
from .request_adaptor import RequestAdaptor
from ..enums import Interaction
from ..params import ParamInfo
from ..request.request import Request
from ..response.response import Response
from ...exceptions import GRPCException
from ...utils import Sync2AsyncUtils

if TYPE_CHECKING:
    from src.grpc_framework.application import GRPCFramework


class _HasRuntimeErrorRemark: ...


class GRPCAdaptor:
    """grpc adaptor, its will adaptation one request dispatch

    Args:
        app: current grpc-framework application
    """

    def __init__(self, app: 'GRPCFramework'):
        self.app = app
        self.s2a = Sync2AsyncUtils(self.app.config.executor)

    def wrap_unary_unary_handler(self, handler: Callable, request_model_type: ParamInfo):
        """wrap unary_unary endpoint"""

        async def wrapper(request_bytes: Any, context: ServicerContext):
            request_adaptor = self.make_request_adaptor(
                request_bytes=request_bytes,
                context=context,
                request_model_type=request_model_type,
                interaction_type=Interaction.unary
            )
            return await self.unary_response(request_adaptor, handler)

        return wrapper

    def wrap_unary_stream_handler(self, handler: Callable, request_model_type: ParamInfo):
        """wrap unary_stream endpoint"""

        async def wrapper(request_bytes: Any, context: ServicerContext):
            request_adaptor = self.make_request_adaptor(
                request_bytes=request_bytes,
                context=context,
                request_model_type=request_model_type,
                interaction_type=Interaction.unary
            )
            async for response in self.stream_response(request_adaptor, handler):
                yield response

        return wrapper

    def wrap_stream_unary_handler(self, handler: Callable, request_model_type: ParamInfo):
        """wrap stream_unary endpoint"""

        async def wrapper(request_bytes: Any, context: ServicerContext):
            request_adaptor = self.make_request_adaptor(
                request_bytes=request_bytes,
                context=context,
                request_model_type=request_model_type,
                interaction_type=Interaction.stream
            )
            return await self.unary_response(request_adaptor, handler)

        return wrapper

    def wrap_stream_stream_handler(self, handler: Callable, request_model_type: ParamInfo):
        """wrap stream_stream endpoint"""

        async def wrapper(request_bytes: Any, context: ServicerContext):
            request_adaptor = self.make_request_adaptor(
                request_bytes=request_bytes,
                context=context,
                request_model_type=request_model_type,
                interaction_type=Interaction.stream
            )
            async for response in self.stream_response(request_adaptor, handler):
                yield response

        return wrapper

    def make_request_adaptor(self,
                             request_bytes: Any,
                             context: ServicerContext,
                             request_model_type: ParamInfo,
                             interaction_type: Interaction) -> RequestAdaptor:
        """make a request adaptor for a once request"""
        request = self.adapt_request(Request.current(), request_bytes, context)
        request_adaptor = RequestAdaptor(
            interaction_type=interaction_type,
            app=self.app,
            request=request,
            input_param_info=request_model_type
        )
        return request_adaptor

    async def unary_response(self, request_adaptor: RequestAdaptor, handler: Callable):
        """handle unary endpoint"""
        request = request_adaptor.request
        async with self.app.start_request_context(request) as ctx:
            async for response in self.call_handler(handler):
                if response is _HasRuntimeErrorRemark:
                    return b''
                response = Response(content=response, app=self.app)
                ctx.send(response)
                self.app.logger.info(
                    f'Call method success: /{request.package}.{request.service_name}/{request.method_name}')
                return response.render()
        raise GRPCException.unknown(f'Can not handle endpoint: {handler}')

    async def stream_response(self, request_adaptor: RequestAdaptor, handler: Callable):
        """handle stream endpoint"""
        request = request_adaptor.request
        async with self.app.start_request_context(request) as ctx:
            async for response in self.call_handler(handler):
                if response is _HasRuntimeErrorRemark:
                    yield b""
                response = Response(content=response, app=self.app)
                ctx.send(response)
                yield response.render()
        self.app.logger.info(
            f'Call method success: /{request.package}.{request.service_name}/{request.method_name}')

    async def call_handler(self, handler: Callable):
        """
        At the end of the request context,
        the processing function is called asynchronously,
        which will convert any function into an asynchronous generator
        """
        if inspect.iscoroutinefunction(handler):
            run_handler = handler
        elif inspect.isgeneratorfunction(handler):
            run_handler = partial(self.s2a.run_generate, gene=handler)
        elif inspect.iscoroutinefunction(handler):
            run_handler = handler
        else:
            async def _to_async_iter(h):
                yield await self.s2a.run_function(h)

            run_handler = partial(_to_async_iter, h=handler)
        try:
            async for response in run_handler():
                yield response
        except Exception as endpoint_runtime_error:
            request = Request.current()
            self.app.logger.exception(endpoint_runtime_error)
            traceback.print_exc()
            self.app._error_handler.call_error_handler(endpoint_runtime_error, request)
            self.app.logger.error(
                f'Call handler error, method: /{request.package}.{request.service_name}/{request.method_name}')
            yield _HasRuntimeErrorRemark

    @staticmethod
    def adapt_request(request: Request, request_data: bytes, context) -> Request:
        """second parse Request：supplement the original request data and context information"""
        # set original request bytes
        request.set_request_bytes(request_data)
        # parse context to request instance
        request.from_context(context)
        # set grpc context
        request.grpc_context = context
        return request
