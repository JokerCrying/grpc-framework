import inspect
from dataclasses import dataclass, field, is_dataclass
from typing import (
    Type, Optional, List, Any, get_origin, Union,
    get_args, Dict, Tuple, get_type_hints
)


@dataclass
class ParamInfo:
    """参数信息类型定义"""
    type: Type
    optional: bool = field(default=False)
    union_types: Optional[List[Type]] = field(default=None)
    generic_args: Optional[List[Type]] = field(default=None)
    annotated_args: Optional[List[Any]] = field(default=None)

    def from_value(self, value: Any) -> Any:
        """
        Serialize the given value to an instance of the current type description
        Now it's an instance method. Just pass in the value parameter
        """
        if value is None:
            return None

        target_type = self.type
        origin = get_origin(target_type) or target_type

        # 处理Optional类型
        if origin is Union:
            args = get_args(target_type)
            if type(None) in args:
                non_none_types = [t for t in args if t is not type(None)]
                if len(non_none_types) == 1:
                    return ParamInfo(
                        type=non_none_types[0],
                        optional=self.optional,
                        union_types=self.union_types,
                        generic_args=self.generic_args,
                        annotated_args=self.annotated_args
                    ).from_value(value)

        # 处理List类型
        if origin is list or origin is List:
            item_type = get_args(target_type)[0]
            return [
                ParamInfo(
                    type=item_type,
                    optional=self.optional,
                    union_types=self.union_types,
                    generic_args=self.generic_args,
                    annotated_args=self.annotated_args
                ).from_value(item)
                for item in value
            ]

        # 处理Dict类型
        if origin is dict or origin is Dict:
            key_type, val_type = get_args(target_type)
            return {
                ParamInfo(
                    type=key_type,
                    optional=self.optional,
                    union_types=self.union_types,
                    generic_args=self.generic_args,
                    annotated_args=self.annotated_args
                ).from_value(k):
                    ParamInfo(
                        type=val_type,
                        optional=self.optional,
                        union_types=self.union_types,
                        generic_args=self.generic_args,
                        annotated_args=self.annotated_args
                    ).from_value(v)
                for k, v in value.items()
            }

        # 处理Tuple类型
        if origin is tuple or origin is Tuple:
            return tuple(
                ParamInfo(
                    type=typ,
                    optional=self.optional,
                    union_types=self.union_types,
                    generic_args=self.generic_args,
                    annotated_args=self.annotated_args
                ).from_value(val)
                for val, typ in zip(value, get_args(target_type))
            )

        # 处理自定义类型
        if isinstance(value, dict):
            # 处理dataclass类型
            if is_dataclass(target_type):
                field_types = get_type_hints(target_type)
                kwargs = {}
                for field_name, field_type in field_types.items():
                    if field_name in value:
                        kwargs[field_name] = ParamInfo(
                            type=field_type,
                            optional=self.optional,
                            union_types=self.union_types,
                            generic_args=self.generic_args,
                            annotated_args=self.annotated_args
                        ).from_value(value[field_name])
                return target_type(**kwargs)

            # 处理TypedDict类型
            if hasattr(target_type, "__annotations__"):
                field_types = target_type.__annotations__
                if not field_types:
                    return value
                kwargs = {}
                for field_name, field_type in field_types.items():
                    if field_name in value:
                        kwargs[field_name] = ParamInfo(
                            type=field_type,
                            optional=self.optional,
                            union_types=self.union_types,
                            generic_args=self.generic_args,
                            annotated_args=self.annotated_args
                        ).from_value(value[field_name])
                return target_type(**kwargs)

            # 处理普通类的__init__方法参数
            if hasattr(target_type, "__init__"):
                init_signature = inspect.signature(target_type.__init__)
                kwargs = {}
                for param_name, param in init_signature.parameters.items():
                    if param_name != "self" and param_name in value:
                        kwargs[param_name] = ParamInfo(
                            type=param.annotation,
                            optional=self.optional,
                            union_types=self.union_types,
                            generic_args=self.generic_args,
                            annotated_args=self.annotated_args
                        ).from_value(value[param_name])
                return target_type(**kwargs)

        # 基本类型直接转换
        return value
