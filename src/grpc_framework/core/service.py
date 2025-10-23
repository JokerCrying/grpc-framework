import inspect
from ..types import OptionalStr
from ..core.enums import Interaction
from typing import TypedDict, Callable, Optional, Type, Union, Dict
from ..core.params import ParamInfo, ParamParser
from ..core.request.request import Request

__all__ = [
    'rpc',
    'RPCFunctionMetadata',
    'Service',
    'unary_stream',
    'unary_unary',
    'stream_unary',
    'stream_stream'
]


class RPCFunctionMetadata(TypedDict):
    handler: Callable
    request_interaction: Interaction
    response_interaction: Interaction
    rpc_service: Optional[Union['Service', Type['Service']]]
    input_param_info: Dict[str, ParamInfo]
    return_param_info: ParamInfo


def rpc(request_interaction: Interaction, response_interaction: Interaction):
    """register a rpc method in a cbv mode."""

    def decorator(func):
        """remark rpc method and record rpc metadata"""
        func.is_rpc_method = True
        func.__rpc_meta__ = {
            'request_interaction': request_interaction,
            'response_interaction': response_interaction
        }
        return func

    return decorator


def unary_unary(func):
    """register a unary_unary method in a cbv mode."""
    return rpc(Interaction.unary, Interaction.unary)(func)


def unary_stream(func):
    """register a unary_stream method in a cbv mode."""
    return rpc(Interaction.unary, Interaction.stream)(func)


def stream_unary(func):
    """register a stream_unary method in a cbv mode."""
    return rpc(Interaction.stream, Interaction.unary)(func)


def stream_stream(func):
    """register a stream_stream method in a cbv mode."""
    return rpc(Interaction.stream, Interaction.stream)(func)


class Service:
    def __init__(self, service_name: OptionalStr = None):
        self.service_name = service_name or self.__class__.__name__
        self._methods = {}
        self.request: Optional[Request] = None

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
                response_interaction=response_interaction,
                rpc_service=self,
                input_param_info=ParamParser.parse_input_params(func),
                return_param_info=ParamParser.parse_return_type(func)
            )
            return func

        return decorator

    def unary_unary(self, func):
        return self.method(Interaction.unary, Interaction.unary)(func)

    def unary_stream(self, func):
        return self.method(Interaction.unary, Interaction.stream)(func)

    def stream_unary(self, func):
        return self.method(Interaction.stream, Interaction.unary)(func)

    def stream_stream(self, func):
        return self.method(Interaction.stream, Interaction.stream)(func)

    @classmethod
    def collect_rpc_methods(cls):
        """CBV collection: Use the @rpc registration method in the scanning class"""
        methods = {}
        for name, func in inspect.getmembers(cls, predicate=inspect.isfunction):
            if getattr(func, "is_rpc_method", False):
                rpc_meta = func.__rpc_meta__
                methods[name] = RPCFunctionMetadata(
                    handler=func,
                    request_interaction=rpc_meta['request_interaction'],
                    response_interaction=rpc_meta['response_interaction'],
                    rpc_service=cls,
                    input_param_info=ParamParser.parse_input_params(func),
                    return_param_info=ParamParser.parse_return_type(func)
                )
        return methods

    def __post_init__(self):
        """step2 initialize Request Class, if you want to override this method, please call super().__post_init__()"""
        self.request = Request.current()
