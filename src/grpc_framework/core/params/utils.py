import inspect
from typing import (
    Any, Dict, List, Optional, Type, TypeVar, Union,
    get_args, get_origin, Callable
)
from typing_extensions import (
    Annotated, get_type_hints as get_extended_type_hints
)
from .domain import ParamInfo

T = TypeVar('T')


class ParamParser:
    """enhanced interface parameter parsing tool class"""

    @staticmethod
    def parse_input_params(func: Callable) -> Dict[str, ParamInfo]:
        """
        Parse the function parameter and return the ParamInfo instance
        :return: {
            "param_name": ParamInfo
        }
        """
        signature = inspect.signature(func)
        type_hints = get_extended_type_hints(func)

        params = {}

        for name, param in signature.parameters.items():
            param_type = type_hints.get(name, Any)
            params[name] = ParamParser._parse_type(param_type)

        return params

    @staticmethod
    def parse_return_type(func: Callable) -> ParamInfo:
        """Parse the function return type and return an instance of ParamInfo"""
        type_hints = get_extended_type_hints(func)
        return_type = type_hints.get('return', Any)
        return ParamParser._parse_type(return_type)

    @staticmethod
    def _parse_type(type_: Type) -> ParamInfo:
        """Parse a single type and return an instance of ParamInfo"""
        return ParamInfo(
            type=type_,
            optional=ParamParser._is_optional(type_),
            union_types=ParamParser._get_union_types(type_),
            generic_args=ParamParser._get_generic_args(type_),
            annotated_args=ParamParser._get_annotated_args(type_)
        )

    @staticmethod
    def _is_optional(type_: Type) -> bool:
        """determine whether it is of the optional type"""
        origin = get_origin(type_)
        if origin is Union:
            args = get_args(type_)
            return type(None) in args
        return False

    @staticmethod
    def _get_union_types(type_: Type) -> Optional[List[Type]]:
        """obtain all types in the union type"""
        origin = get_origin(type_)
        if origin is Union:
            return [t for t in get_args(type_) if t is not type(None)]
        return None

    @staticmethod
    def _get_generic_args(type_: Type) -> Optional[List[Type]]:
        """obtain generic parameters"""
        origin = get_origin(type_)
        if origin is not None and origin not in (Union, Optional):
            return list(get_args(type_))
        return None

    @staticmethod
    def _get_annotated_args(type_: Type) -> Optional[List[Any]]:
        """get the parameter of the annotated type"""
        origin = get_origin(type_)
        if origin is Annotated:
            return list(get_args(type_)[1:])
        return None
