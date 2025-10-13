import inspect
from ..types import OptionalStr
from .enums import Interaction
from typing import TypedDict, Callable

__all__ = [
    'rpc',
    'RPCFunctionMetadata',
    'Service'
]


def rpc(request_interaction: Interaction, response_interaction: Interaction):
    def decorator(func):
        func.is_rpc_method = True
        func.__rpc_meta__ = {
            'request_interaction': request_interaction,
            'response_interaction': response_interaction
        }
        return func

    return decorator


class RPCFunctionMetadata(TypedDict):
    handler: Callable
    request_interaction: Interaction
    response_interaction: Interaction


class Service:
    def __init__(self, service_name: OptionalStr = None):
        self.service_name = service_name or self.__class__.__name__
        self._methods = {}

    @property
    def methods(self):
        return self._methods

    def method(self, request_interaction: Interaction, response_interaction: Interaction):
        def decorator(func):
            func_name = func.__name__
            if func_name in self._methods:
                raise ValueError(f'The handler `{func_name}` has already in {self.service_name}')
            self._methods[func_name] = RPCFunctionMetadata(
                handler=func,
                request_interaction=request_interaction,
                response_interaction=response_interaction
            )
            return func

        return decorator

    @classmethod
    def collect_rpc_methods(cls):
        """CBV collection: Use the @rpc registration method in the scanning class"""
        methods = {}
        for name, func in inspect.getmembers(cls, predicate=inspect.isfunction):
            if getattr(func, "is_rpc_method", False):
                methods[name] = RPCFunctionMetadata(
                    handler=func,
                    request_interaction=func.__rpc_meta__['request_interaction'],
                    response_interaction=func.__rpc_meta__['response_interaction']
                )
        return methods
