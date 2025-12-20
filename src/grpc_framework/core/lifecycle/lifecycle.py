import inspect
import asyncio
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Callable


class SyncToAsyncGeneratorAdapter:
    def __init__(self, func):
        self.func = func

    async def __call__(self, *args, **kwargs):
        for item in self.func(*args, **kwargs):
            yield item


class LifecycleManager:
    def __init__(self, executor: Optional[ThreadPoolExecutor]):
        self.executor = executor
        self._lifecycle_handler: Optional[Callable] = None
        self._startup_handlers = []
        self._shutdown_handlers = []
        self._loop = None
        self.is_before_run = False
        self.is_after_run = False

    def set_loop(self, loop):
        self._loop = loop

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
        self._lifecycle_handler = func
        return func

    async def startup(self, app):
        await self._run_hooks(app, self._startup_handlers)
        self.is_before_run = True

    async def shutdown(self, app):
        await self._run_hooks(app, self._shutdown_handlers)
        self.is_after_run = True

    @asynccontextmanager
    async def context(self, app):
        if self._lifecycle_handler:
            target_func = self._lifecycle_handler
            if inspect.isgeneratorfunction(target_func):
                target_func = SyncToAsyncGeneratorAdapter(target_func)
            cm_factory = asynccontextmanager(target_func)

            async with cm_factory(app):
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

    async def _run_hooks(self, app, hooks):
        for fn in hooks:
            if asyncio.iscoroutinefunction(fn):
                await fn(app)
            else:
                loop = self._loop or asyncio.get_running_loop()
                await loop.run_in_executor(self.executor, fn, app)

    def update_executor(self, executor: ThreadPoolExecutor):
        self.executor = executor
