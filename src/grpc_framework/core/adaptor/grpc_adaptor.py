import inspect
from grpc.aio import ServicerContext
from typing import Optional, Sequence, TYPE_CHECKING, Any, Callable
from ...utils import Sync2AsyncUtils
from ..request.request import Request
from ..response.response import Response
from ..enums import Interaction
from .request_adaptor import RequestAdaptor
from functools import partial

if TYPE_CHECKING:
    from src.grpc_framework.application import GRPCFramework


class GRPCAdaptor:
    """grpc adaptor, its will adaptation one request dispatch

    Args:
        app: current grpc-framework application
    """

    def __init__(self, app: 'GRPCFramework'):
        self.app = app
        self.s2a = Sync2AsyncUtils(self.app.config.executor)

    def wrap_unary_unary_handler(self, handler: Callable, request_model_type: type):
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

    def wrap_unary_stream_handler(self, handler: Callable, request_model_type: type):
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

    def wrap_stream_unary_handler(self, handler: Callable, request_model_type: type):
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

    def wrap_stream_stream_unary_handler(self, handler: Callable, request_model_type: type):
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

    def wrap_handler_by_interaction(self, handler: Callable, request_interaction, response_interaction,
                                    request_model_type: type, response_model_type: type):
        """Select the appropriate wrapper based on the type of interaction"""
        if request_interaction == Interaction.unary and response_interaction == Interaction.unary:
            return self.wrap_unary_unary_handler(handler, request_model_type, response_model_type)
        elif request_interaction == Interaction.unary and response_interaction == Interaction.stream:
            return self.wrap_unary_stream_handler(handler, request_model_type, response_model_type)
        elif request_interaction == Interaction.stream and response_interaction == Interaction.unary:
            return self.wrap_stream_unary_handler(handler, request_model_type, response_model_type)
        elif request_interaction == Interaction.stream and response_interaction == Interaction.stream:
            return self.wrap_stream_stream_handler(handler, request_model_type, response_model_type)
        else:
            raise ValueError(f"Unsupported interaction types: {request_interaction}, {response_interaction}")

    def make_request_adaptor(self,
                             request_bytes: Any,
                             context: ServicerContext,
                             request_model_type: type,
                             interaction_type: Interaction) -> RequestAdaptor:
        """make a request adaptor for a once request"""
        request = self.adapt_request(Request.current(), request_bytes, context)
        request_adaptor = RequestAdaptor(
            interaction_type=interaction_type,
            app=self.app,
            request=request,
            model_type=request_model_type
        )
        return request_adaptor

    async def unary_response(self, request_adaptor: RequestAdaptor, handler: Callable):
        """handle unary endpoint"""
        async with self.app.start_request_context(request_adaptor.request) as ctx:
            async for response in self.call_handler(handler):
                response = Response(content=response, app=self.app)
                ctx.send(response)
                return response.render()
        raise RuntimeError(f'Can not handle endpoint: {handler}')

    async def stream_response(self, request_adaptor: RequestAdaptor, handler: Callable):
        """handle stream endpoint"""
        async with self.app.start_request_context(request_adaptor.request) as ctx:
            async for response in self.call_handler(handler):
                response = Response(content=response, app=self.app)
                ctx.send(response)
                yield response.render()

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
        async for response in run_handler():
            yield response

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
