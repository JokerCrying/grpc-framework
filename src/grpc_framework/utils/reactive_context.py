from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import Callable, Tuple, Any


class ReactiveContextMinix:
    def __init__(self, before_hooks: Callable, after_hooks: Callable, before_args: Tuple[Any]):
        self.before_hooks = before_hooks
        self.after_hooks = after_hooks
        self.before_args = before_args
        self.active = True


class ReactiveContext(ReactiveContextMinix, AbstractContextManager):
    def __enter__(self):
        self.before_hooks(*self.before_args)
        return self

    def __exit__(self, exc_type, exc_value, traceback, /):
        self.active = False
        self.after_hooks(None)

    def send(self, value):
        if not self.active:
            raise RuntimeError('Context has already stop.')
        self.after_hooks(value)


class AsyncReactiveContext(ReactiveContextMinix, AbstractAsyncContextManager):
    async def __aenter__(self):
        await self.before_hooks(*self.before_args)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback, /):
        self.active = False

    async def send(self, value):
        if not self.active:
            raise RuntimeError('AsyncContext has already stop.')
        await self.after_hooks(value)
