import asyncio
import inspect
from .middleware import BaseMiddleware
from ..request.request import Request
from .. import RPCFunctionMetadata
from ..enums import Interaction
from typing import Callable


class HandlerMiddleware(BaseMiddleware):
    async def dispatch(self, request: 'Request', call_next: Callable):
        handler_meta = self.app.find_endpoint(request.package, request.service_name, request.method_name)

    async def context(self, request: "Request", handler_meta: RPCFunctionMetadata):
        for call in self.app.before_request_hooks:
            call(request)
        # TODO: 这里需要开始调用处理了，需要将原始请求通过序列化器转为对应的DomainModel，然后调用执行器
        # TODO: 且需要同时支持请求方式为unary和stream的方式，以及处理响应方式，例如unary和stream
