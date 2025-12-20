from typing import Any, Callable, Optional, TypeVar, Generic

T = TypeVar("T")


class Depends(Generic[T]):
    """
    Dependency injection marker.

    Usage:
        def endpoint(db: Depends[DBFactory]): ...
        def endpoint(db: DBFactory = Depends(get_db)): ...
    """

    def __init__(self, dependency: Optional[Callable[..., Any]] = None, use_cache: bool = True):
        self.dependency = dependency
        self.use_cache = use_cache

    def __repr__(self):
        attr = getattr(self.dependency, "__name__", type(self.dependency).__name__)
        cache = "" if self.use_cache else ", use_cache=False"
        return f"{self.__class__.__name__}({attr}{cache})"
