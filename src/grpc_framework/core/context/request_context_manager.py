import inspect
from typing import Optional, TYPE_CHECKING, Callable, Any, List
from ...utils import Sync2AsyncUtils, AsyncReactiveContext

if TYPE_CHECKING:
    from ...application import GRPCFramework
    from ..request.request import Request

BEFORE_HOOK_TYPE = Callable[[Request], Any]
AFTER_HOOK_TYPE = Callable[[Any], Any]


class RequestContextManager:
    def __init__(self, app: 'GRPCFramework'):
        self.app = app
        self.s2a = Sync2AsyncUtils(self.app.config.executor)
        self._before_request_handlers: List[BEFORE_HOOK_TYPE] = []
        self._after_request_handlers: List[AFTER_HOOK_TYPE] = []

    def before_request(self, func: BEFORE_HOOK_TYPE):
        self._before_request_handlers.append(BEFORE_HOOK_TYPE)
        return func

    def after_request(self, func: AFTER_HOOK_TYPE):
        self._after_request_handlers.append(func)
        return func

    async def context(self, request: Request):
        return AsyncReactiveContext(
            self.on_before_request,
            self.on_after_request,
            (request,)
        )

    async def on_before_request(self, request: Request):
        for call in self._before_request_handlers:
            if inspect.iscoroutinefunction(call):
                await call(request)
            else:
                await self.s2a.run_function(call, request)

    async def on_after_request(self, response):
        for call in self._after_request_handlers:
            if inspect.iscoroutinefunction(call):
                await call(response)
            else:
                await self.s2a.run_function(call, response)
