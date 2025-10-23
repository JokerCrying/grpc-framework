import abc
import asyncio
import inspect
from typing import Callable, TYPE_CHECKING
from ..request import Request

if TYPE_CHECKING:
    from ...application import GRPCFramework


class BaseMiddleware(metaclass=abc.ABCMeta):
    def __init__(self, app: 'GRPCFramework'):
        self.app = app

    @abc.abstractmethod
    async def dispatch(self, request: Request, call_next: Callable):
        raise NotImplementedError


class MiddlewareManager:
    def __init__(self, app: 'GRPCFramework'):
        self.app = app
        self._middlewares = []

    def add_middleware(self, middleware: BaseMiddleware):
        self._middlewares.append(middleware)

    async def dispatch(self, request: 'Request', handler):
        """construct the middleware call chain"""

        async def call_next(req: 'Request'):
            if not callable(handler):
                return None
            return await handler(req)

        # reverse parcel middleware chain
        for mw in reversed(self._middlewares):
            if asyncio.iscoroutinefunction(mw):
                # functional middleware
                next_handler = call_next

                async def call_next(req, _mw=mw, _next=next_handler):
                    return await _mw(req, _next)
            elif inspect.isclass(mw) and issubclass(mw, BaseMiddleware):
                # class based middleware
                mw_instance = mw(self.app)
                next_handler = call_next

                async def call_next(req, _mw_inst=mw_instance, _next=next_handler):
                    return await _mw_inst.dispatch(req, _next)
            else:
                raise TypeError(f"Invalid middleware type: {mw}")
        return await call_next(request)
