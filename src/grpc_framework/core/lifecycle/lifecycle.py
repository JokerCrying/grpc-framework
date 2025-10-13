import inspect
import asyncio
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Callable, AsyncGenerator, Generator


class LifecycleManager:
    def __init__(self, executor: ThreadPoolExecutor):
        self.executor = executor
        self._lifecycle_ctx = None
        self._startup_handlers = []
        self._shutdown_handlers = []
        self._loop = asyncio.get_event_loop()

    def on_startup(self, func: Callable):
        self._startup_handlers.append(func)
        return func

    def on_shutdown(self, func: Callable):
        self._shutdown_handlers.append(func)
        return func

    def lifecycle(self, func: Callable):
        if not inspect.isasyncgenfunction(func) and not inspect.isgeneratorfunction(func):
            raise ValueError(f'The lifecycle handler must be a generator function or async generator function.')
        if inspect.isgeneratorfunction(func):
            func = self.async_iter_wrapper(func)
        self._lifecycle_ctx = asynccontextmanager(func)

    async def startup(self, app):
        for fn in self._startup_handlers:
            if asyncio.iscoroutinefunction(fn):
                await fn(app)
            else:
                await self._loop.run_in_executor(self.executor, fn, app)

    async def shutdown(self, app):
        for fn in reversed(self._shutdown_handlers):
            if asyncio.iscoroutinefunction(fn):
                await fn(app)
            else:
                await self._loop.run_in_executor(self.executor, fn, app)

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
