import inspect
from functools import partial
from typing import TYPE_CHECKING, Any
from grpc.aio import ServicerContext
from .request_adaptor import RequestAdaptor
from .response_adaptor import ResponseAdaptor
from ..enums import Interaction
from ..params import ParamInfo
from ..request.request import Request
from ..response.response import Response
from ...exceptions import GRPCException
from ...utils import Sync2AsyncUtils
from ..service import RPCFunctionMetadata
from concurrent.futures import ThreadPoolExecutor

if TYPE_CHECKING:
    from ...application import GRPCFramework


class GRPCAdaptor:
    """grpc adaptor, its will adaptation one request dispatch

    Args:
        app: current grpc-framework application
    """

    def __init__(self, app: 'GRPCFramework'):
        self.app = app
        self.s2a = None

    def wrap_unary_unary_handler(self, rpc_metadata: RPCFunctionMetadata):
        """wrap unary_unary endpoint"""

        async def wrapper(request_bytes: Any, context: ServicerContext):
            request_adaptor = self.make_request_adaptor(
                request_bytes=request_bytes,
                context=context,
                request_metadata=rpc_metadata,
                interaction_type=Interaction.unary
            )
            await self.app.dispatch(request_adaptor.request, request_adaptor.request.grpc_context)
            return await self.unary_response(request_adaptor, rpc_metadata)

        return wrapper

    def wrap_unary_stream_handler(self, rpc_metadata: RPCFunctionMetadata):
        """wrap unary_stream endpoint"""

        async def wrapper(request_bytes: Any, context: ServicerContext):
            request_adaptor = self.make_request_adaptor(
                request_bytes=request_bytes,
                context=context,
                request_metadata=rpc_metadata,
                interaction_type=Interaction.unary
            )
            await self.app.dispatch(request_adaptor.request, request_adaptor.request.grpc_context)
            async for response in self.stream_response(request_adaptor, rpc_metadata):
                yield response

        return wrapper

    def wrap_stream_unary_handler(self, rpc_metadata: RPCFunctionMetadata):
        """wrap stream_unary endpoint"""

        async def wrapper(request_bytes: Any, context: ServicerContext):
            request_adaptor = self.make_request_adaptor(
                request_bytes=request_bytes,
                context=context,
                request_metadata=rpc_metadata,
                interaction_type=Interaction.stream
            )
            await self.app.dispatch(request_adaptor.request, request_adaptor.request.grpc_context)
            return await self.unary_response(request_adaptor, rpc_metadata)

        return wrapper

    def wrap_stream_stream_handler(self, rpc_metadata: RPCFunctionMetadata):
        """wrap stream_stream endpoint"""

        async def wrapper(request_bytes: Any, context: ServicerContext):
            request_adaptor = self.make_request_adaptor(
                request_bytes=request_bytes,
                context=context,
                request_metadata=rpc_metadata,
                interaction_type=Interaction.stream
            )
            await self.app.dispatch(request_adaptor.request, request_adaptor.request.grpc_context)
            async for response in self.stream_response(request_adaptor, rpc_metadata):
                yield response

        return wrapper

    def make_request_adaptor(self,
                             request_bytes: Any,
                             context: ServicerContext,
                             interaction_type: Interaction,
                             request_metadata: RPCFunctionMetadata) -> RequestAdaptor:
        """make a request adaptor for a once request"""
        request = self.adapt_request(Request.current(), request_bytes, context)
        request.current_request_metadata = request_metadata
        request_adaptor = RequestAdaptor(
            interaction_type=interaction_type,
            app=self.app,
            request=request,
            input_param_info=request_metadata['input_param_info']
        )
        return request_adaptor

    async def unary_response(self, request_adaptor: RequestAdaptor, rpc_metadata: RPCFunctionMetadata):
        """handle unary endpoint"""
        request = request_adaptor.request
        async with self.app.start_request_context(request) as ctx:
            async for response in self.call_handler(rpc_metadata, request_adaptor):
                response = Response(content=response, app=self.app)
                response_adaptor = ResponseAdaptor(
                    app=self.app,
                    response=response,
                    request=request,
                    ctx=ctx
                )
                response_content = await response_adaptor.get_response()
                return response_content
        raise GRPCException.unknown(f'Can not handle endpoint: {rpc_metadata["handler"]}')

    async def stream_response(self, request_adaptor: RequestAdaptor, rpc_metadata: RPCFunctionMetadata):
        """handle stream endpoint"""
        request = request_adaptor.request
        async with self.app.start_request_context(request) as ctx:
            async for response in self.call_handler(rpc_metadata, request_adaptor):
                response = Response(content=response, app=self.app)
                response_adaptor = ResponseAdaptor(
                    app=self.app,
                    response=response,
                    request=request,
                    ctx=ctx
                )
                response_content = await response_adaptor.get_response()
                yield response_content

    async def call_handler(self, run_metadata: RPCFunctionMetadata, request_adaptor: RequestAdaptor):
        """
        At the end of the request context,
        the processing function is called asynchronously,
        which will convert any function into an asynchronous generator
        """
        try:
            handler = run_metadata['handler']
            params = self.get_run_handler_args(run_metadata, request_adaptor)
            if inspect.iscoroutinefunction(handler):
                # async function
                async def _to_async_iter(h):
                    yield await h(**params)

                run_handler = partial(_to_async_iter, h=handler)
            elif inspect.isgeneratorfunction(handler):
                # generator
                run_handler = partial(self.s2a.run_generate, gene=handler, *(params.values()))
            elif inspect.isasyncgenfunction(handler):
                run_handler = partial(handler, **params)
            else:
                async def _sync_to_async_iter(h):
                    yield await self.s2a.run_function(h, *(params.values()))

                run_handler = partial(_sync_to_async_iter, h=handler)
            async for response in run_handler():
                yield response
        except Exception as endpoint_runtime_error:
            self.app.logger.exception(endpoint_runtime_error)
            yield endpoint_runtime_error

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

    @classmethod
    def get_run_handler_args(cls, metadata: RPCFunctionMetadata, request_adaptor: RequestAdaptor):
        result = {}
        input_params = metadata['input_param_info']
        if inspect.isclass(metadata['rpc_service']):
            # cbv mode
            rpc_service_class = metadata['rpc_service']
            service_instance = rpc_service_class()
            service_instance.__post_init__()  # call post init
            for index, key in enumerate(input_params.keys()):
                if index == 0:
                    result[key] = service_instance
                    continue
                param_info = input_params[key]
                result[key] = cls.transport_request_args(param_info, request_adaptor, key)
        else:
            # root service or fbv mode
            for key in input_params.keys():
                param_info = input_params[key]
                result[key] = cls.transport_request_args(param_info, request_adaptor, key)
        return result

    @staticmethod
    def transport_request_args(param_info: ParamInfo, request_adaptor: RequestAdaptor, key: str):
        try:
            return request_adaptor.request_model(key)
        except Exception as e:
            if param_info.optional:
                return None
            else:
                raise GRPCException.invalid_argument(
                    detail=f"The server can't parse some data for type {param_info.type}") from e

    def init_s2a(self, executor: ThreadPoolExecutor):
        self.s2a = Sync2AsyncUtils(executor)
