import contextlib
from typing import Dict, Any, Type, Optional, Callable, Union
from .depends import Depends
from .provider import DependencyProvider
from ...utils.sync2async_utils import Sync2AsyncUtils


class DependencyContainer:
    """
    Global Dependency Container.
    Stores the mapping between dependency keys (types or functions) and their Providers.
    """

    def __init__(self):
        self._providers: Dict[Any, DependencyProvider] = {}

    def register(self, key: Any, factory: Callable):
        """Register a dependency factory for a given key."""
        self._providers[key] = DependencyProvider(factory)

    def get_provider(self, key: Any) -> Optional[DependencyProvider]:
        return self._providers.get(key)

    def scope(self, s2a: Sync2AsyncUtils) -> "DependencyScope":
        """Create a new dependency scope."""
        return DependencyScope(self, s2a)


class DependencyScope:
    """
    Dependency Resolution Scope.
    Manages the lifecycle of dependencies within a single request or context.
    Ensures that scoped dependencies are singletons within the scope.
    """

    def __init__(self, container: DependencyContainer, s2a: Sync2AsyncUtils):
        self.container = container
        self.s2a = s2a
        self._cache: Dict[Any, Any] = {}
        self.exit_stack = contextlib.AsyncExitStack()

    async def resolve(self, dependency: Union[Depends, Callable, Type]) -> Any:
        """
        Resolve a dependency.
        
        Args:
            dependency: Can be a Depends object, a factory function, or a type.
        """
        # Unwrap Depends object
        if isinstance(dependency, Depends):
            key = dependency.dependency
            use_cache = dependency.use_cache
        else:
            key = dependency
            use_cache = True

        # Check cache if enabled
        if use_cache and key in self._cache:
            return self._cache[key]

        # Get provider
        provider = self.container.get_provider(key)
        if not provider:
            # If not explicitly registered, try to use the key itself as the factory
            # This supports direct usage like Depends(get_db) without pre-registration
            if callable(key):
                provider = DependencyProvider(key)
            else:
                raise ValueError(f"No provider found for dependency: {key}")

        # Resolve sub-dependencies recursively
        sub_values = {}
        for param_name, sub_dep in provider.sub_dependencies.items():
            sub_values[param_name] = await self.resolve(sub_dep)

        # Call provider
        instance = await provider.call(sub_values, self.exit_stack, self.s2a)

        # Cache result if enabled
        if use_cache:
            self._cache[key] = instance

        return instance

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.exit_stack.aclose()
