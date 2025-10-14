import asyncio
from concurrent.futures import Executor
from typing import Optional, Callable


class Sync2AsyncUtils:
    def __init__(
            self,
            executor: Optional[Executor] = None
    ):
        self.executor = executor
        self.loop = asyncio.get_event_loop()

    async def run_function(self, func: Callable, *args):
        """run a bio function in event loop"""
        return await self.loop.run_in_executor(self.executor, func, *args)

    async def run_generate(self, gene: Callable, *args):
        """run a bio generator in event loop
        warning: its will the performance overhead is very high if generate so many item
        """
        sync_iter = await self.loop.run_in_executor(self.executor, gene, *args)
        while True:
            try:
                item = await self.loop.run_in_executor(self.executor, next, sync_iter)
                yield item
            except (StopIteration, RuntimeError):
                break
