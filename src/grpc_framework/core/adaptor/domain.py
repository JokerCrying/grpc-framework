from typing import Any, Optional, Callable, Generic, AsyncIterator
from ...types import AsyncIteratorType, T


class StreamRequest(Generic[T]):
    """a type tips for define a grpc stream request

    eg.
    >>> from dataclasses import dataclass
    >>> @dataclass
    >>> class User:
    >>>     id: int
    >>>
    >>> async def user_request(request: StreamRequest[User]):
    >>>     async for item in request:
    >>>         print(item.id)

    """

    def __init__(self,
                 request_iter: AsyncIteratorType[Any],
                 deserialization_handler: Callable,
                 model_type: Optional[T] = None):
        self.request_iter = request_iter
        self.deserialization_handler = deserialization_handler
        self.model_type = model_type

    async def __aiter__(self) -> AsyncIterator[T]:
        async for item in self.request_iter:
            yield self.deserialization_handler(item, self.model_type)
