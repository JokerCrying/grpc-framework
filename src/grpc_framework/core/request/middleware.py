from typing import Any, Callable
from .request import Request
from ..middleware import BaseMiddleware


class RequestContextMiddleware(BaseMiddleware):
    async def dispatch(self, context, call_next: Callable):
        request_instance = Request.from_grpc_context(context)
        return await call_next(request_instance)
