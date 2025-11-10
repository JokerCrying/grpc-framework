import inspect
import asyncio
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Callable


class LifecycleManager:
    def __init__(self, executor: ThreadPoolExecutor):
        self.executor = executor
        self._lifecycle_ctx = None
        self._startup_handlers = []
        self._shutdown_handlers = []
        self._loop = asyncio.get_event_loop()
        self.is_before_run = False
        self.is_after_run = False

    def on_startup(self, func: Callable, index: Optional[int] = None):
        if index is not None:
            self._startup_handlers.insert(index, func)
        else:
            self._startup_handlers.append(func)
        return func

    def on_shutdown(self, func: Callable, index: Optional[int] = None):
        if index is not None:
            self._shutdown_handlers.insert(index, func)
        else:
            self._shutdown_handlers.append(func)
        return func

    def lifecycle(self, func: Callable):
        if not inspect.isasyncgenfunction(func) and not inspect.isgeneratorfunction(func):
            raise ValueError(f'The lifecycle handler must be a generator function or async generator function.')
        if inspect.isgeneratorfunction(func):
            func = self.async_iter_wrapper(func)
        self._lifecycle_ctx = asynccontextmanager(func)

    async def startup(self, app):
        await self._run_hooks(app, self._startup_handlers)
        self.is_before_run = True

    async def shutdown(self, app):
        await self._run_hooks(app, self._shutdown_handlers)
        self.is_after_run = True

    @asynccontextmanager
    async def context(self, app):
        """最终统一生命周期上下文"""
        if self._lifecycle_ctx:
            async with self._lifecycle_ctx(app):
                await self.startup(app)
                try:
                    yield
                finally:
                    await self.shutdown(app)
        else:
            await self.startup(app)
            try:
                yield
            finally:
                await self.shutdown(app)

    @staticmethod
    def async_iter_wrapper(func: Callable):
        async def wrapper(*args, **kwargs):
            for item in func(*args, **kwargs):
                yield item

        return wrapper

    async def _run_hooks(self, app, hooks):
        for fn in hooks:
            if asyncio.iscoroutinefunction(fn):
                await fn(app)
            else:
                await self._loop.run_in_executor(self.executor, fn, app)
