import grpc
import inspect
from typing import TYPE_CHECKING, Dict, Callable, Type, Any
from .request.request import Request
from ..utils import Sync2AsyncUtils
from ..exceptions import GRPCException
from concurrent.futures import ThreadPoolExecutor

if TYPE_CHECKING:
    from ..application import GRPCFramework


class ErrorHandler:
    def __init__(self, app: 'GRPCFramework'):
        self.app = app
        self._error_handlers: Dict[Type[Exception], Callable[[Request, Exception], Any]] = {
            GRPCException: self.common_error_handler
        }
        self.s2a = None

    def add_error_handler(self, exc_type: Type[Exception]):
        """add a handler for handle exception with exception type"""

        def wrapper(func: Callable[[Request, Exception], None]):
            self._error_handlers[exc_type] = func
            return func

        return wrapper

    async def call_error_handler(self, exc: Exception, request: Request):
        """call exception handler with a runtime endpoint exception instance"""
        exc_type = exc.__class__
        if exc_type not in self._error_handlers:
            handler = self.common_error_handler
        else:
            handler = self._error_handlers[exc_type]
        if inspect.iscoroutinefunction(handler):
            return await handler(request, exc)
        else:
            return await self.s2a.run_function(handler, request, exc)

    @staticmethod
    async def common_error_handler(request: Request, exc: Exception):
        request.grpc_context.set_code(grpc.StatusCode.INTERNAL)
        request.grpc_context.set_details(f'Internal Error: {exc}')

    @staticmethod
    async def grpc_error_handler(request: Request, exc: GRPCException):
        request.grpc_context.set_code(exc.code)
        request.grpc_context.set_details(f'Internal Error: {exc.detail}')

    def init_s2a(self, executor: ThreadPoolExecutor):
        self.s2a = Sync2AsyncUtils(executor)
