import inspect
import contextlib
from typing import Callable, Any, Dict, List, Optional, Tuple, AsyncGenerator
from .depends import Depends
from ..params import ParamParser, ParamInfo
from ...utils.sync2async_utils import Sync2AsyncUtils


class DependencyProvider:
    """
    Dependency Provider that handles the resolution and execution of dependency factories.
    It supports:
    - Sync functions
    - Async functions
    - Sync generators (via thread pool)
    - Async generators
    """

    def __init__(self, dependency: Callable[..., Any]):
        self.dependency = dependency
        self.is_generator = inspect.isgeneratorfunction(dependency)
        self.is_async_generator = inspect.isasyncgenfunction(dependency)
        self.is_coroutine = inspect.iscoroutinefunction(dependency)
        
        # Parse sub-dependencies once during initialization
        self.sub_dependencies: Dict[str, Depends] = self._analyze_dependencies(dependency)

    def _analyze_dependencies(self, func: Callable) -> Dict[str, Depends]:
        """Analyze the function signature to find Depends markers."""
        deps = {}
        signature = inspect.signature(func)
        param_infos = ParamParser.parse_input_params(func)
        
        for name, param in signature.parameters.items():
            # Check default value: func(dep: T = Depends(factory))
            if isinstance(param.default, Depends):
                deps[name] = param.default
                continue
            
            # Check annotation: func(dep: Depends[Factory])
            # Note: We rely on ParamParser's logic, but here we need to inspect the raw annotation or ParamInfo
            # Since Depends is a Generic, we need to check if the type is a Depends instance or subclass
            # However, ParamParser returns ParamInfo. Let's inspect the raw type from ParamInfo if possible
            # Or re-inspect using get_type_hints if needed.
            # Simplified approach: Check if param_info.type is a Depends generic or similar.
            
            # Since Depends[T] is a type, not an instance, we need to handle it.
            # But the user's example shows `db: Depends[DBFactory]`.
            # We need to extract `DBFactory` from `Depends[DBFactory]`.
            
            annotation = param.annotation
            if hasattr(annotation, "__origin__") and annotation.__origin__ is Depends:
                args = getattr(annotation, "__args__", [])
                if args:
                    dependency_factory = args[0]
                    deps[name] = Depends(dependency=dependency_factory)
        
        return deps

    async def call(
        self, 
        values: Dict[str, Any], 
        stack: contextlib.AsyncExitStack,
        s2a: Sync2AsyncUtils
    ) -> Any:
        """
        Call the dependency factory with resolved values.
        Manages lifecycle for generators using the exit stack.
        """
        if self.is_async_generator:
            cm = contextlib.asynccontextmanager(self.dependency)(**values)
            return await stack.enter_async_context(cm)
            
        elif self.is_generator:
            # For sync generators, we need to run next() in thread pool
            # and ensure close() is also run in thread pool
            cm = self._sync_generator_wrapper(self.dependency, values, s2a)
            return await stack.enter_async_context(cm)
            
        elif self.is_coroutine:
            return await self.dependency(**values)
            
        else:
            # Sync function
            return await s2a.run_function(self.dependency, *values.values())

    @staticmethod
    @contextlib.asynccontextmanager
    async def _sync_generator_wrapper(
        func: Callable, 
        kwargs: Dict[str, Any], 
        s2a: Sync2AsyncUtils
    ):
        """Wraps a sync generator to run in a thread pool via Sync2AsyncUtils."""
        # Use run_generate to create the generator and yield the first item
        async_gen = s2a.run_generate(func, *kwargs.values())
        
        try:
            # Get the yielded value (resource)
            res = await async_gen.__anext__()
            yield res
        except StopAsyncIteration:
             raise RuntimeError("Generator did not yield any value")
        except Exception:
            raise
        finally:
             # Clean up the rest of the generator (teardown)
             # We just need to exhaust or close it. 
             # Since run_generate yields items, if we stop iterating, 
             # the generator inside run_generate might be garbage collected or closed?
             # But run_generate's implementation loops until StopIteration.
             # If we stop here, the `run_generate` coroutine is suspended at `yield item`.
             # We need to ensure the sync generator's finally block runs.
             
             # Actually, s2a.run_generate iterates the sync generator in the executor.
             # But it doesn't expose a way to explicitly close the sync generator from here easily
             # without iterating it to the end.
             # And standard dependency injection patterns usually yield once.
             # So we expect one yield, then return/end.
             
             # Let's try to finish the generator
             try:
                 await async_gen.__anext__()
             except StopAsyncIteration:
                 pass
             except Exception:
                 # If the generator raises an error during teardown
                 pass

