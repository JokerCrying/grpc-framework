import grpc
import grpc.aio as grpc_aio
from typing import TYPE_CHECKING, Callable, Awaitable
from ..request.request import Request

if TYPE_CHECKING:
    from ...application import GRPCFramework


class RequestContextInterceptor(grpc_aio.ServerInterceptor):
    def __init__(self, app: 'GRPCFramework'):
        self.app = app

    async def intercept_service(self, continuation: Callable[
        [grpc.HandlerCallDetails], Awaitable[grpc.RpcMethodHandler]
    ], handler_call_details: grpc.HandlerCallDetails):
        # 初步解析Request
        request = Request()
        request.from_handler_details(handler_call_details)
        return await continuation(handler_call_details)
