from __future__ import annotations

import os
import sys
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    Set,
    Callable,
    Awaitable,
    Coroutine,
    AsyncIterable,
    AsyncIterator,
    TextIO,
    BinaryIO,
    NewType,
    Protocol,
    runtime_checkable,
    get_args,
    get_origin,
    TYPE_CHECKING,
    Type
)

if sys.version_info >= (3, 10):
    from typing import TypeAlias, ParamSpec, Concatenate
else:
    from typing_extensions import TypeAlias, ParamSpec, Concatenate

if sys.version_info >= (3, 11):
    from typing import Self, Never
else:
    from typing_extensions import Self, Never

# 类型变量
T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)
T_contra = TypeVar('T_contra', contravariant=True)
KT = TypeVar('KT')  # Key type
VT = TypeVar('VT')  # Value type
P = ParamSpec('P')  # Parameter specification
TypeT = Type[T]

# 路径相关类型
PathLike = Union[str, os.PathLike]
PathLikeStr = Union[str, bytes]
FilePath = PathLike
DirPath = PathLike
ModulePath = FilePath

# JSON 相关类型
JSONPrimitive = Union[str, int, float, bool, None]
JSONType = Union[JSONPrimitive, Dict[str, Any], List[Any]]
JSONDict = Dict[str, JSONType]
JSONList = List[JSONType]

# 数字类型
Number = Union[int, float]
IntFloat = Union[int, float]
DecimalType = Union[int, float, str]

# 集合类型
StrSet = Set[str]
IntSet = Set[int]
StrList = List[str]
IntList = List[int]
StrTuple = Tuple[str, ...]
IntTuple = Tuple[int, ...]

# 可调用类型
Predicate = Callable[[T], bool]
Comparator = Callable[[T, T], int]
Mapper = Callable[[T], Any]
Consumer = Callable[[T], None]
Supplier = Callable[[], T]
Factory = Callable[..., T]

# 异步类型
AsyncCallable = Callable[..., Awaitable[T]]
AsyncPredicate = Callable[[T], Awaitable[bool]]
AsyncMapper = Callable[[T], Awaitable[Any]]
AsyncConsumer = Callable[[T], Awaitable[None]]

# IO 类型
FileDescriptor = int
TextStream = TextIO
BinaryStream = BinaryIO
AnyStream = Union[TextStream, BinaryStream]

# 协程和异步迭代器
CoroutineType = Coroutine[Any, Any, T]
AsyncIteratorType = AsyncIterator[T]
AsyncIterableType = AsyncIterable[T]

# 字典类型
StrDict = Dict[str, T]
AnyDict = Dict[str, Any]
StrAnyDict = Dict[str, Any]
IntStrDict = Dict[int, str]
StrIntDict = Dict[str, int]

# 可选类型
OptionalStr = Optional[str]
OptionalInt = Optional[int]
OptionalFloat = Optional[float]
OptionalBool = Optional[bool]
OptionalList = Optional[List[T]]
OptionalDict = Optional[Dict[KT, VT]]
OptionalT = Optional[T]

# 字节类型
BytesLike = Union[bytes, bytearray]


# 协议定义
@runtime_checkable
class SupportsRead(Protocol[T]):
    def read(self) -> T: ...


@runtime_checkable
class SupportsWrite(Protocol[T]):
    def write(self, data: T) -> Any: ...


@runtime_checkable
class SupportsClose(Protocol):
    def close(self) -> Any: ...


@runtime_checkable
class SupportsReadWriteClose(Protocol[T]):
    def read(self) -> T: ...

    def write(self, data: T) -> Any: ...

    def close(self) -> Any: ...


# 泛型容器类型
Maybe = Union[T, None]
OneOrMany = Union[T, Sequence[T]]
OneOrManyOptional = Union[OptionalT, Sequence[OptionalT]]
DictOrList = Union[Dict[KT, VT], List[VT]]
DictOrTuple = Union[Dict[KT, VT], Tuple[VT, ...]]

# 时间类型
Timestamp = Union[int, float]
DatetimeLike = Union[str, int, float]

# 其他常用类型
URL = str
Email = str
UUIDString = str
Base64String = str
HexString = str
RegexPattern = str
HTMLString = str
XMLString = str
SQLString = str

# 类型别名
if sys.version_info >= (3, 10):
    # Python 3.10+ 可以使用 TypeAlias
    Json: TypeAlias = Union[
        Dict[str, "Json"],
        List["Json"],
        str,
        int,
        float,
        bool,
        None
    ]
    Matrix: TypeAlias = List[List[T]]
    Vector: TypeAlias = List[T]
    Tensor: TypeAlias = Union[T, List[T], List[List[T]], List[List[List[T]]]]
else:
    Json = Union[Dict[str, Any], List[Any], str, int, float, bool, None]
    Matrix = List[List[T]]
    Vector = List[T]
    Tensor = Union[T, List[T], List[List[T]], List[List[List[T]]]]

# 静态类型检查时的一些辅助类型
if TYPE_CHECKING:
    import datetime
    import decimal
    import uuid

    DateTime = Union[datetime.datetime, str, int, float]
    Date = Union[datetime.date, str]
    Time = Union[datetime.time, str]
    Decimal = decimal.Decimal
    UUID = uuid.UUID
else:
    DateTime = Any
    Date = Any
    Time = Any
    Decimal = Any
    UUID = Any


# 类型转换工具函数
def get_optional_type(t: type[T]) -> type[Optional[T]]:
    """获取可选类型的内部类型"""
    origin = get_origin(t)
    if origin is Union:
        args = get_args(t)
        if type(None) in args and len(args) == 2:
            return args[0] if args[1] is type(None) else args[1]
    return t


def is_optional_type(t: type) -> bool:
    """检查类型是否为 Optional[T]"""
    origin = get_origin(t)
    return origin is Union and type(None) in get_args(t)


def is_list_type(t: type) -> bool:
    """检查类型是否为 List[T]"""
    origin = get_origin(t)
    return origin is list or origin is List


def is_dict_type(t: type) -> bool:
    """检查类型是否为 Dict[K, V]"""
    origin = get_origin(t)
    return origin is dict or origin is Dict
